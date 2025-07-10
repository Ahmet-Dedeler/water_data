from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_

from app.models.search_system import (
    SearchQueryLog,
    SavedSearchFilter,
    SearchAnalytics,
    RecommendationIndex,
    SearchableEntityType,
    RecommendationSource,
    SearchResultItem,
    SearchResponse
)
from app.schemas.search_system import (
    SearchQueryLogCreate,
    SavedSearchFilterCreate,
    SavedSearchFilterSchema
)
# Import other models needed for searching
from app.models.user import User
from app.models.water import Water
from app.models.drink import Drink
from app.models.health_goal import HealthGoal

class SearchSystemService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(
        self,
        user_id: int,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20
    ) -> SearchResponse:
        """
        Performs a comprehensive search across multiple entities.
        In a real-world scenario, this would likely query a dedicated search engine
        like Elasticsearch or OpenSearch. This implementation simulates it with SQL.
        """
        if filters is None:
            filters = {}
        
        results: List[SearchResultItem] = []
        
        # Determine which entity types to search
        allowed_types_str = filters.get("types", [])
        if isinstance(allowed_types_str, str):
            allowed_types_str = [allowed_types_str]

        search_types = [SearchableEntityType(t) for t in allowed_types_str] if allowed_types_str else list(SearchableEntityType)

        # Simulate a federated search
        if SearchableEntityType.USER in search_types:
            results.extend(await self._search_users(query))
        if SearchableEntityType.DRINK in search_types:
            results.extend(await self._search_drinks(query))
        if SearchableEntityType.HEALTH_GOAL in search_types:
            results.extend(await self._search_health_goals(query))
        
        # In a real system, you'd have a more sophisticated ranking algorithm
        # For now, we sort by a simulated score (could be based on match quality)
        results.sort(key=lambda r: r.score, reverse=True)
        
        total_count = len(results)
        paginated_results = results[(page - 1) * page_size : page * page_size]
        
        # Log the search query
        log_entry = await self.log_search_query(user_id, query, filters, total_count)
        
        # Get suggestions (placeholder)
        suggestions = await self.get_query_suggestions(query)
        
        return SearchResponse(
            query_id=log_entry.id,
            results=paginated_results,
            suggestions=suggestions,
            total_count=total_count
        )

    async def log_search_query(self, user_id: int, query: str, filters: Dict, result_count: int) -> SearchQueryLog:
        log_create = SearchQueryLogCreate(query_text=query, filters=filters)
        log = SearchQueryLog(
            user_id=user_id,
            query_text=log_create.query_text,
            filters=log_create.filters,
            result_count=result_count
        )
        self.db.add(log)
        
        # Update analytics
        await self._update_search_analytics(query)
        
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def get_recommendations(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        Retrieves pre-computed recommendations for a user.
        A background job would be responsible for populating the RecommendationIndex.
        """
        result = await self.db.execute(
            select(RecommendationIndex)
            .filter(RecommendationIndex.user_id == user_id)
            .order_by(RecommendationIndex.score.desc())
            .limit(limit)
        )
        recommendations = result.scalars().all()
        # Here you would fetch the actual entity details based on type and id
        # This is a simplified representation
        return [
            {"type": r.recommended_entity_type.value, "id": r.recommended_entity_id, "score": r.score}
            for r in recommendations
        ]

    async def create_saved_filter(self, user_id: int, filter_data: SavedSearchFilterCreate) -> SavedSearchFilter:
        new_filter = SavedSearchFilter(user_id=user_id, **filter_data.dict())
        self.db.add(new_filter)
        await self.db.commit()
        await self.db.refresh(new_filter)
        return new_filter

    async def get_saved_filters(self, user_id: int) -> List[SavedSearchFilterSchema]:
        result = await self.db.execute(
            select(SavedSearchFilter).filter(SavedSearchFilter.user_id == user_id)
        )
        return result.scalars().all()

    async def get_query_suggestions(self, partial_query: str) -> List[str]:
        """
        Provides autocomplete suggestions based on popular or recent queries.
        """
        if not partial_query:
            return []
        
        result = await self.db.execute(
            select(SearchAnalytics.query_text)
            .filter(SearchAnalytics.query_text.ilike(f"{partial_query}%"))
            .order_by(SearchAnalytics.search_frequency.desc())
            .limit(5)
        )
        return result.scalars().all()

    # --- Private Search Helpers ---

    async def _search_users(self, query: str) -> List[SearchResultItem]:
        results = []
        stmt = select(User).filter(
            or_(
                User.username.ilike(f"%{query}%"),
                User.email.ilike(f"%{query}%")
            )
        )
        db_results = await self.db.execute(stmt)
        for user in db_results.scalars().all():
            results.append(SearchResultItem(
                entity_type=SearchableEntityType.USER,
                entity_id=user.id,
                title=user.username,
                description=f"User profile for {user.username}",
                score=0.9, # Simulated score
                metadata={"email": user.email, "join_date": str(user.created_at)}
            ))
        return results

    async def _search_drinks(self, query: str) -> List[SearchResultItem]:
        results = []
        stmt = select(Drink).filter(Drink.name.ilike(f"%{query}%"))
        db_results = await self.db.execute(stmt)
        for drink in db_results.scalars().all():
            results.append(SearchResultItem(
                entity_type=SearchableEntityType.DRINK,
                entity_id=drink.id,
                title=drink.name,
                description=f"A type of beverage.",
                score=0.8,
                metadata={"caffeine": drink.caffeine, "sugar": drink.sugar}
            ))
        return results
        
    async def _search_health_goals(self, query: str) -> List[SearchResultItem]:
        results = []
        stmt = select(HealthGoal).filter(
            or_(
                HealthGoal.name.ilike(f"%{query}%"),
                HealthGoal.description.ilike(f"%{query}%")
            )
        )
        db_results = await self.db.execute(stmt)
        for goal in db_results.scalars().all():
            results.append(SearchResultItem(
                entity_type=SearchableEntityType.HEALTH_GOAL,
                entity_id=goal.id,
                title=goal.name,
                description=goal.description,
                score=0.85,
                metadata={"target": goal.target, "deadline": str(goal.deadline)}
            ))
        return results

    async def _update_search_analytics(self, query: str):
        result = await self.db.execute(
            select(SearchAnalytics).filter(SearchAnalytics.query_text == query)
        )
        analytics_entry = result.scalars().first()

        if analytics_entry:
            analytics_entry.search_frequency += 1
            analytics_entry.last_searched = func.now()
        else:
            analytics_entry = SearchAnalytics(query_text=query)
            self.db.add(analytics_entry)
        
        await self.db.flush() 