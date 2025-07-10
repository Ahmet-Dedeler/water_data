from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Enum,
    Boolean,
    Text,
    JSON
)
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field
import enum

Base = declarative_base()

# Enum for different searchable entities
class SearchableEntityType(enum.Enum):
    USER = "user"
    WATER_LOG = "water_log"
    DRINK = "drink"
    INGREDIENT = "ingredient"
    ACHIEVEMENT = "achievement"
    HEALTH_GOAL = "health_goal"
    ARTICLE = "article"
    SOCIAL_POST = "social_post"

# Enum for recommendation sources
class RecommendationSource(enum.Enum):
    COLLABORATIVE_FILTERING = "collaborative_filtering"
    CONTENT_BASED = "content_based"
    TRENDING = "trending"
    PERSONALIZED_POPULARITY = "personalized_popularity"

# --- SQLAlchemy Models ---

class SearchQueryLog(Base):
    __tablename__ = "search_query_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    query_text = Column(String, index=True, nullable=False)
    filters = Column(JSON)  # e.g., {"type": "user", "location": "CA"}
    result_count = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")

class SavedSearchFilter(Base):
    __tablename__ = "saved_search_filters"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    filters = Column(JSON, nullable=False)
    
    user = relationship("User")

class SearchAnalytics(Base):
    __tablename__ = "search_analytics"
    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(String, index=True, unique=True)
    search_frequency = Column(Integer, default=1)
    click_through_rate = Column(Integer, default=0) # Represented as an integer, e.g., 25 for 25%
    last_searched = Column(DateTime, default=datetime.utcnow)

class RecommendationIndex(Base):
    __tablename__ = "recommendation_index"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    recommended_entity_type = Column(Enum(SearchableEntityType), nullable=False)
    recommended_entity_id = Column(Integer, nullable=False)
    score = Column(Integer) # Higher is better
    source = Column(Enum(RecommendationSource))
    generated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

# --- Pydantic Schemas ---

class SearchQueryLogBase(BaseModel):
    query_text: str
    filters: Optional[Dict[str, Any]] = None

class SearchQueryLogCreate(SearchQueryLogBase):
    pass

class SearchQueryLogSchema(SearchQueryLogBase):
    id: int
    user_id: int
    result_count: int
    timestamp: datetime

    class Config:
        orm_mode = True

class SearchResultItem(BaseModel):
    entity_type: SearchableEntityType
    entity_id: int
    title: str
    description: Optional[str] = None
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SearchResponse(BaseModel):
    query_id: Optional[int]
    results: List[SearchResultItem]
    suggestions: List[str] = Field(default_factory=list)
    total_count: int

class SavedSearchFilterBase(BaseModel):
    name: str
    filters: Dict[str, Any]

class SavedSearchFilterCreate(SavedSearchFilterBase):
    pass

class SavedSearchFilterSchema(SavedSearchFilterBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True

class RecommendationSchema(BaseModel):
    entity_type: SearchableEntityType
    entity_id: int
    title: str
    description: Optional[str] = None
    reason: Optional[str] = None # e.g., "Because you liked..."
    source: RecommendationSource

    class Config:
        orm_mode = True 