"""
Service for health app integration with Apple Health, Google Fit, and other platforms.
"""

import json
import logging
import uuid
from collections import defaultdict
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from statistics import mean, median
import asyncio

from app.models.health_integration import (
    HealthIntegration, HealthMetric, SyncSession, HealthDataMapping,
    HealthDataConflict, HealthInsight, HealthGoalIntegration,
    HealthPlatform, DataType, SyncStatus, PermissionLevel, SyncFrequency
)
from app.schemas.health_integration import (
    HealthIntegrationCreate, HealthIntegrationUpdate, HealthMetricCreate,
    HealthMetricUpdate, SyncRequest, HealthMetricQuery, ConflictResolution,
    HealthInsightFeedback, HealthGoalIntegrationCreate, HealthGoalIntegrationUpdate,
    HealthDataMappingCreate, HealthDataMappingUpdate, BulkHealthMetricCreate,
    HealthIntegrationFilter, SyncSessionFilter, HealthInsightFilter
)
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class HealthIntegrationService(BaseService):
    """Service for managing health app integrations and data synchronization."""

    def __init__(self):
        super().__init__()
        self.data_dir = Path("app/data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Data files
        self.integrations_file = self.data_dir / "health_integrations.json"
        self.metrics_file = self.data_dir / "health_metrics.json"
        self.sync_sessions_file = self.data_dir / "sync_sessions.json"
        self.mappings_file = self.data_dir / "health_data_mappings.json"
        self.conflicts_file = self.data_dir / "health_data_conflicts.json"
        self.insights_file = self.data_dir / "health_insights.json"
        self.goal_integrations_file = self.data_dir / "health_goal_integrations.json"
        
        # Initialize default mappings
        self._initialize_default_mappings()

    async def _load_data(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load data from JSON file."""
        if not file_path.exists():
            return []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading data from {file_path}: {e}")
            return []

    async def _save_data(self, file_path: Path, data: List[Dict[str, Any]]):
        """Save data to JSON file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving data to {file_path}: {e}")
            raise

    def _initialize_default_mappings(self):
        """Initialize default platform data mappings."""
        if self.mappings_file.exists():
            return
            
        default_mappings = [
            # Apple Health mappings
            {
                "id": str(uuid.uuid4()),
                "platform": "apple_health",
                "platform_data_type": "HKQuantityTypeIdentifierDietaryWater",
                "internal_data_type": "water_intake",
                "value_field": "value",
                "unit_field": "unit",
                "timestamp_field": "startDate",
                "value_multiplier": 1000.0,  # Convert L to mL
                "value_offset": 0.0,
                "unit_conversion": {"L": "mL", "fl_oz": "mL"},
                "min_value": 0.0,
                "max_value": 10000.0,
                "required_fields": ["value", "startDate"],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "is_active": True
            },
            {
                "id": str(uuid.uuid4()),
                "platform": "apple_health",
                "platform_data_type": "HKQuantityTypeIdentifierStepCount",
                "internal_data_type": "steps",
                "value_field": "value",
                "unit_field": "unit",
                "timestamp_field": "startDate",
                "value_multiplier": 1.0,
                "value_offset": 0.0,
                "unit_conversion": {},
                "min_value": 0.0,
                "max_value": 100000.0,
                "required_fields": ["value", "startDate"],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "is_active": True
            },
            # Google Fit mappings
            {
                "id": str(uuid.uuid4()),
                "platform": "google_fit",
                "platform_data_type": "com.google.hydration",
                "internal_data_type": "water_intake",
                "value_field": "fpVal",
                "unit_field": None,
                "timestamp_field": "startTimeNanos",
                "value_multiplier": 1000.0,  # Convert L to mL
                "value_offset": 0.0,
                "unit_conversion": {},
                "min_value": 0.0,
                "max_value": 10000.0,
                "required_fields": ["fpVal", "startTimeNanos"],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "is_active": True
            },
            {
                "id": str(uuid.uuid4()),
                "platform": "google_fit",
                "platform_data_type": "com.google.step_count.delta",
                "internal_data_type": "steps",
                "value_field": "intVal",
                "unit_field": None,
                "timestamp_field": "startTimeNanos",
                "value_multiplier": 1.0,
                "value_offset": 0.0,
                "unit_conversion": {},
                "min_value": 0.0,
                "max_value": 100000.0,
                "required_fields": ["intVal", "startTimeNanos"],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "is_active": True
            }
        ]
        
        try:
            with open(self.mappings_file, 'w', encoding='utf-8') as f:
                json.dump(default_mappings, f, indent=2, ensure_ascii=False)
            logger.info(f"Initialized {len(default_mappings)} default health data mappings")
        except Exception as e:
            logger.error(f"Error initializing default mappings: {e}")

    # Health Integration Management
    async def create_integration(
        self,
        user_id: int,
        integration_data: HealthIntegrationCreate
    ) -> HealthIntegration:
        """Create a new health platform integration."""
        integrations = await self._load_data(self.integrations_file)
        
        # Check if integration already exists
        existing = next((i for i in integrations if i['user_id'] == user_id and i['platform'] == integration_data.platform), None)
        if existing:
            raise ValueError(f"Integration with {integration_data.platform} already exists for user")
        
        # Initialize permissions based on enabled data types
        permissions = {}
        for data_type in integration_data.enabled_data_types:
            permissions[data_type] = PermissionLevel.READ_ONLY
        
        integration = HealthIntegration(
            id=str(uuid.uuid4()),
            user_id=user_id,
            permissions=permissions,
            **integration_data.dict()
        )
        
        integrations.append(integration.dict())
        await self._save_data(self.integrations_file, integrations)
        
        logger.info(f"Created health integration {integration.id} for user {user_id} with platform {integration.platform}")
        return integration

    async def get_integration(self, integration_id: str) -> Optional[HealthIntegration]:
        """Get a specific health integration."""
        integrations = await self._load_data(self.integrations_file)
        integration_data = next((i for i in integrations if i['id'] == integration_id), None)
        return HealthIntegration(**integration_data) if integration_data else None

    async def update_integration(
        self,
        integration_id: str,
        user_id: int,
        update_data: HealthIntegrationUpdate
    ) -> Optional[HealthIntegration]:
        """Update a health integration."""
        integrations = await self._load_data(self.integrations_file)
        integration_index = next((i for i, integration in enumerate(integrations) if integration['id'] == integration_id and integration['user_id'] == user_id), None)
        
        if integration_index is None:
            return None
        
        update_dict = update_data.dict(exclude_unset=True)
        
        # Update permissions if enabled_data_types changed
        if 'enabled_data_types' in update_dict:
            permissions = {}
            for data_type in update_dict['enabled_data_types']:
                permissions[data_type] = PermissionLevel.READ_ONLY
            update_dict['permissions'] = permissions
        
        integrations[integration_index].update(update_dict)
        integrations[integration_index]['updated_at'] = datetime.utcnow().isoformat()
        
        await self._save_data(self.integrations_file, integrations)
        
        logger.info(f"Updated health integration {integration_id}")
        return HealthIntegration(**integrations[integration_index])

    async def delete_integration(self, integration_id: str, user_id: int) -> bool:
        """Delete a health integration."""
        integrations = await self._load_data(self.integrations_file)
        initial_len = len(integrations)
        
        integrations = [i for i in integrations if not (i['id'] == integration_id and i['user_id'] == user_id)]
        
        if len(integrations) < initial_len:
            await self._save_data(self.integrations_file, integrations)
            logger.info(f"Deleted health integration {integration_id}")
            return True
        return False

    async def get_user_integrations(
        self,
        user_id: int,
        filter_data: Optional[HealthIntegrationFilter] = None
    ) -> List[HealthIntegration]:
        """Get all health integrations for a user."""
        integrations = await self._load_data(self.integrations_file)
        user_integrations = [HealthIntegration(**i) for i in integrations if i['user_id'] == user_id]
        
        # Apply filters
        if filter_data:
            if filter_data.platforms:
                user_integrations = [i for i in user_integrations if i.platform in filter_data.platforms]
            if filter_data.is_connected is not None:
                user_integrations = [i for i in user_integrations if i.is_connected == filter_data.is_connected]
            if filter_data.is_active is not None:
                user_integrations = [i for i in user_integrations if i.is_active == filter_data.is_active]
            if filter_data.has_errors is not None:
                if filter_data.has_errors:
                    user_integrations = [i for i in user_integrations if i.last_error]
                else:
                    user_integrations = [i for i in user_integrations if not i.last_error]
            if filter_data.data_types:
                user_integrations = [i for i in user_integrations if any(dt in i.enabled_data_types for dt in filter_data.data_types)]
        
        return user_integrations

    # Health Metrics Management
    async def create_metric(
        self,
        user_id: int,
        metric_data: HealthMetricCreate
    ) -> HealthMetric:
        """Create a new health metric."""
        metrics = await self._load_data(self.metrics_file)
        
        metric = HealthMetric(
            id=str(uuid.uuid4()),
            **metric_data.dict()
        )
        
        # Check for conflicts with existing data
        conflicts = await self._detect_conflicts(user_id, metric)
        if conflicts:
            await self._save_conflicts(conflicts)
        
        metrics.append(metric.dict())
        await self._save_data(self.metrics_file, metrics)
        
        logger.info(f"Created health metric {metric.id} for user {user_id}")
        return metric

    async def get_metric(self, metric_id: str) -> Optional[HealthMetric]:
        """Get a specific health metric."""
        metrics = await self._load_data(self.metrics_file)
        metric_data = next((m for m in metrics if m['id'] == metric_id), None)
        return HealthMetric(**metric_data) if metric_data else None

    async def update_metric(
        self,
        metric_id: str,
        update_data: HealthMetricUpdate
    ) -> Optional[HealthMetric]:
        """Update a health metric."""
        metrics = await self._load_data(self.metrics_file)
        metric_index = next((i for i, m in enumerate(metrics) if m['id'] == metric_id), None)
        
        if metric_index is None:
            return None
        
        update_dict = update_data.dict(exclude_unset=True)
        metrics[metric_index].update(update_dict)
        metrics[metric_index]['updated_at'] = datetime.utcnow().isoformat()
        
        await self._save_data(self.metrics_file, metrics)
        
        logger.info(f"Updated health metric {metric_id}")
        return HealthMetric(**metrics[metric_index])

    async def query_metrics(
        self,
        user_id: int,
        query: HealthMetricQuery,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[HealthMetric], int]:
        """Query health metrics with filtering."""
        metrics = await self._load_data(self.metrics_file)
        
        # Filter by user (implicit)
        # Note: In a real implementation, we'd need to associate metrics with users
        filtered_metrics = []
        
        for metric_data in metrics:
            metric = HealthMetric(**metric_data)
            
            # Apply filters
            if query.data_types and metric.data_type not in query.data_types:
                continue
            if query.platforms and metric.source_platform not in query.platforms:
                continue
            if query.start_date and metric.timestamp < query.start_date:
                continue
            if query.end_date and metric.timestamp > query.end_date:
                continue
            if query.min_confidence and metric.confidence_score < query.min_confidence:
                continue
            if query.validated_only and not metric.is_validated:
                continue
            
            if not query.include_raw_data:
                metric.raw_data = None
            
            filtered_metrics.append(metric)
        
        # Sort by timestamp (newest first)
        filtered_metrics.sort(key=lambda m: m.timestamp, reverse=True)
        
        total = len(filtered_metrics)
        paginated_metrics = filtered_metrics[skip:skip + limit]
        
        return paginated_metrics, total

    async def bulk_create_metrics(
        self,
        user_id: int,
        bulk_data: BulkHealthMetricCreate
    ) -> Tuple[List[HealthMetric], List[Dict[str, Any]], List[HealthDataConflict]]:
        """Create multiple health metrics in bulk."""
        created_metrics = []
        failed_metrics = []
        all_conflicts = []
        
        for metric_data in bulk_data.metrics:
            try:
                metric = await self.create_metric(user_id, metric_data)
                created_metrics.append(metric)
                
                # Check for conflicts if enabled
                if bulk_data.resolve_conflicts:
                    conflicts = await self._detect_conflicts(user_id, metric)
                    all_conflicts.extend(conflicts)
                    
            except Exception as e:
                failed_metrics.append({
                    "metric_data": metric_data.dict(),
                    "error": str(e)
                })
        
        return created_metrics, failed_metrics, all_conflicts

    # Data Synchronization
    async def start_sync(
        self,
        integration_id: str,
        user_id: int,
        sync_request: SyncRequest
    ) -> SyncSession:
        """Start a data synchronization session."""
        integration = await self.get_integration(integration_id)
        if not integration or integration.user_id != user_id:
            raise ValueError("Integration not found or access denied")
        
        if not integration.is_connected:
            raise ValueError("Integration is not connected")
        
        sync_sessions = await self._load_data(self.sync_sessions_file)
        
        session = SyncSession(
            id=str(uuid.uuid4()),
            integration_id=integration_id,
            user_id=user_id,
            platform=integration.platform,
            **sync_request.dict()
        )
        
        sync_sessions.append(session.dict())
        await self._save_data(self.sync_sessions_file, sync_sessions)
        
        # Start the actual sync process in background
        asyncio.create_task(self._perform_sync(session))
        
        logger.info(f"Started sync session {session.id} for integration {integration_id}")
        return session

    async def _perform_sync(self, session: SyncSession):
        """Perform the actual data synchronization."""
        try:
            # Update session status
            await self._update_sync_session(session.id, {"status": SyncStatus.IN_PROGRESS})
            
            # Get platform-specific sync logic
            sync_result = await self._sync_platform_data(session)
            
            # Update session with results
            update_data = {
                "status": SyncStatus.COMPLETED,
                "completed_at": datetime.utcnow().isoformat(),
                "duration_seconds": (datetime.utcnow() - session.started_at).total_seconds(),
                **sync_result
            }
            
            await self._update_sync_session(session.id, update_data)
            
            logger.info(f"Completed sync session {session.id}")
            
        except Exception as e:
            logger.error(f"Sync session {session.id} failed: {e}")
            await self._update_sync_session(session.id, {
                "status": SyncStatus.FAILED,
                "completed_at": datetime.utcnow().isoformat(),
                "errors": [str(e)]
            })

    async def _sync_platform_data(self, session: SyncSession) -> Dict[str, Any]:
        """Sync data from specific platform (mock implementation)."""
        # This would contain platform-specific API calls
        # For now, we'll simulate the sync process
        
        await asyncio.sleep(2)  # Simulate API calls
        
        # Mock sync results
        return {
            "records_processed": 50,
            "records_imported": 45,
            "records_updated": 3,
            "records_skipped": 2,
            "records_failed": 0,
            "summary": f"Successfully synced {session.platform} data"
        }

    async def _update_sync_session(self, session_id: str, update_data: Dict[str, Any]):
        """Update a sync session."""
        sync_sessions = await self._load_data(self.sync_sessions_file)
        session_index = next((i for i, s in enumerate(sync_sessions) if s['id'] == session_id), None)
        
        if session_index is not None:
            sync_sessions[session_index].update(update_data)
            await self._save_data(self.sync_sessions_file, sync_sessions)

    async def get_sync_sessions(
        self,
        user_id: int,
        filter_data: Optional[SyncSessionFilter] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[SyncSession], int]:
        """Get sync sessions for a user."""
        sync_sessions = await self._load_data(self.sync_sessions_file)
        user_sessions = [SyncSession(**s) for s in sync_sessions if s['user_id'] == user_id]
        
        # Apply filters
        if filter_data:
            if filter_data.platforms:
                user_sessions = [s for s in user_sessions if s.platform in filter_data.platforms]
            if filter_data.status:
                user_sessions = [s for s in user_sessions if s.status in filter_data.status]
            if filter_data.date_from:
                user_sessions = [s for s in user_sessions if s.started_at >= filter_data.date_from]
            if filter_data.date_to:
                user_sessions = [s for s in user_sessions if s.started_at <= filter_data.date_to]
            if filter_data.integration_ids:
                user_sessions = [s for s in user_sessions if s.integration_id in filter_data.integration_ids]
        
        # Sort by start time (newest first)
        user_sessions.sort(key=lambda s: s.started_at, reverse=True)
        
        total = len(user_sessions)
        paginated_sessions = user_sessions[skip:skip + limit]
        
        return paginated_sessions, total

    # Conflict Detection and Resolution
    async def _detect_conflicts(self, user_id: int, new_metric: HealthMetric) -> List[HealthDataConflict]:
        """Detect conflicts with existing data."""
        conflicts = []
        
        # Get existing metrics for the same data type and timestamp
        metrics = await self._load_data(self.metrics_file)
        existing_metrics = [
            HealthMetric(**m) for m in metrics
            if m.get('data_type') == new_metric.data_type and
            abs((datetime.fromisoformat(m['timestamp']) - new_metric.timestamp).total_seconds()) < 300  # Within 5 minutes
        ]
        
        if len(existing_metrics) > 0:
            # Create conflict record
            values = []
            for metric in existing_metrics:
                values.append({
                    "value": metric.value,
                    "unit": metric.unit,
                    "source_platform": metric.source_platform,
                    "source_device": metric.source_device,
                    "confidence_score": metric.confidence_score,
                    "metric_id": metric.id
                })
            
            # Add new metric value
            values.append({
                "value": new_metric.value,
                "unit": new_metric.unit,
                "source_platform": new_metric.source_platform,
                "source_device": new_metric.source_device,
                "confidence_score": new_metric.confidence_score,
                "metric_id": new_metric.id
            })
            
            conflict = HealthDataConflict(
                id=str(uuid.uuid4()),
                user_id=user_id,
                data_type=new_metric.data_type,
                timestamp=new_metric.timestamp,
                values=values
            )
            
            conflicts.append(conflict)
        
        return conflicts

    async def _save_conflicts(self, conflicts: List[HealthDataConflict]):
        """Save detected conflicts."""
        all_conflicts = await self._load_data(self.conflicts_file)
        
        for conflict in conflicts:
            all_conflicts.append(conflict.dict())
        
        await self._save_data(self.conflicts_file, all_conflicts)

    async def get_conflicts(
        self,
        user_id: int,
        unresolved_only: bool = True
    ) -> List[HealthDataConflict]:
        """Get data conflicts for a user."""
        conflicts = await self._load_data(self.conflicts_file)
        user_conflicts = [HealthDataConflict(**c) for c in conflicts if c['user_id'] == user_id]
        
        if unresolved_only:
            user_conflicts = [c for c in user_conflicts if not c.is_resolved]
        
        return user_conflicts

    async def resolve_conflict(
        self,
        conflict_id: str,
        user_id: int,
        resolution: ConflictResolution
    ) -> Optional[HealthDataConflict]:
        """Resolve a data conflict."""
        conflicts = await self._load_data(self.conflicts_file)
        conflict_index = next((i for i, c in enumerate(conflicts) if c['id'] == conflict_id and c['user_id'] == user_id), None)
        
        if conflict_index is None:
            return None
        
        conflict_data = conflicts[conflict_index]
        
        # Apply resolution strategy
        if resolution.resolution_strategy == "highest_confidence":
            values = conflict_data['values']
            best_value = max(values, key=lambda v: v.get('confidence_score', 0))
            resolved_value = best_value['value']
        elif resolution.resolution_strategy == "average":
            values = [v['value'] for v in conflict_data['values']]
            resolved_value = sum(values) / len(values)
        elif resolution.resolution_strategy == "manual_select":
            resolved_value = conflict_data['values'][resolution.selected_value_index]['value']
        elif resolution.resolution_strategy == "custom_value":
            resolved_value = resolution.custom_value
        else:
            raise ValueError(f"Unknown resolution strategy: {resolution.resolution_strategy}")
        
        # Update conflict
        conflict_data.update({
            "resolution_strategy": resolution.resolution_strategy,
            "resolved_value": resolved_value,
            "resolved_at": datetime.utcnow().isoformat(),
            "resolved_by": "manual",
            "is_resolved": True
        })
        
        await self._save_data(self.conflicts_file, conflicts)
        
        logger.info(f"Resolved conflict {conflict_id} with strategy {resolution.resolution_strategy}")
        return HealthDataConflict(**conflict_data)

    # Health Insights Generation
    async def generate_insights(self, user_id: int) -> List[HealthInsight]:
        """Generate AI-powered health insights for a user."""
        insights = []
        
        # Get user's health data
        query = HealthMetricQuery(
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow(),
            validated_only=True
        )
        metrics, _ = await self.query_metrics(user_id, query, limit=1000)
        
        if not metrics:
            return insights
        
        # Generate different types of insights
        insights.extend(await self._generate_trend_insights(user_id, metrics))
        insights.extend(await self._generate_correlation_insights(user_id, metrics))
        insights.extend(await self._generate_goal_insights(user_id, metrics))
        
        # Save insights
        all_insights = await self._load_data(self.insights_file)
        for insight in insights:
            all_insights.append(insight.dict())
        await self._save_data(self.insights_file, all_insights)
        
        return insights

    async def _generate_trend_insights(self, user_id: int, metrics: List[HealthMetric]) -> List[HealthInsight]:
        """Generate trend-based insights."""
        insights = []
        
        # Group metrics by data type
        data_by_type = defaultdict(list)
        for metric in metrics:
            data_by_type[metric.data_type].append(metric)
        
        for data_type, type_metrics in data_by_type.items():
            if len(type_metrics) < 7:  # Need at least a week of data
                continue
            
            # Sort by timestamp
            type_metrics.sort(key=lambda m: m.timestamp)
            
            # Calculate trend
            values = [m.value for m in type_metrics]
            if len(values) > 1:
                # Simple trend calculation
                first_half = values[:len(values)//2]
                second_half = values[len(values)//2:]
                
                first_avg = mean(first_half)
                second_avg = mean(second_half)
                
                change_percent = ((second_avg - first_avg) / first_avg) * 100 if first_avg > 0 else 0
                
                if abs(change_percent) > 10:  # Significant change
                    trend_direction = "increased" if change_percent > 0 else "decreased"
                    
                    insight = HealthInsight(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        title=f"Your {data_type.replace('_', ' ').title()} Has {trend_direction.title()}",
                        description=f"Over the past 30 days, your {data_type.replace('_', ' ')} has {trend_direction} by {abs(change_percent):.1f}%.",
                        insight_type="trend",
                        data_types_used=[data_type],
                        platforms_used=list(set(m.source_platform for m in type_metrics)),
                        date_range_start=(datetime.utcnow() - timedelta(days=30)).date(),
                        date_range_end=datetime.utcnow().date(),
                        confidence_score=0.8,
                        actionable_recommendations=[
                            f"Continue monitoring your {data_type.replace('_', ' ')} trends",
                            "Consider setting specific goals to maintain or improve this trend"
                        ],
                        supporting_data={
                            "change_percent": change_percent,
                            "first_period_avg": first_avg,
                            "second_period_avg": second_avg,
                            "data_points": len(values)
                        }
                    )
                    
                    insights.append(insight)
        
        return insights

    async def _generate_correlation_insights(self, user_id: int, metrics: List[HealthMetric]) -> List[HealthInsight]:
        """Generate correlation-based insights."""
        insights = []
        
        # Simple correlation between water intake and steps
        water_metrics = [m for m in metrics if m.data_type == DataType.WATER_INTAKE]
        step_metrics = [m for m in metrics if m.data_type == DataType.STEPS]
        
        if len(water_metrics) > 5 and len(step_metrics) > 5:
            # Group by date and calculate correlation (simplified)
            water_by_date = defaultdict(float)
            steps_by_date = defaultdict(float)
            
            for metric in water_metrics:
                date_key = metric.timestamp.date()
                water_by_date[date_key] += metric.value
            
            for metric in step_metrics:
                date_key = metric.timestamp.date()
                steps_by_date[date_key] += metric.value
            
            # Find common dates
            common_dates = set(water_by_date.keys()) & set(steps_by_date.keys())
            
            if len(common_dates) > 5:
                water_values = [water_by_date[date] for date in common_dates]
                step_values = [steps_by_date[date] for date in common_dates]
                
                # Simple correlation calculation
                if len(water_values) == len(step_values):
                    water_avg = mean(water_values)
                    steps_avg = mean(step_values)
                    
                    numerator = sum((w - water_avg) * (s - steps_avg) for w, s in zip(water_values, step_values))
                    water_var = sum((w - water_avg) ** 2 for w in water_values)
                    steps_var = sum((s - steps_avg) ** 2 for s in step_values)
                    
                    if water_var > 0 and steps_var > 0:
                        correlation = numerator / (water_var * steps_var) ** 0.5
                        
                        if abs(correlation) > 0.5:  # Moderate correlation
                            direction = "positive" if correlation > 0 else "negative"
                            
                            insight = HealthInsight(
                                id=str(uuid.uuid4()),
                                user_id=user_id,
                                title=f"Water Intake and Steps Show {direction.title()} Correlation",
                                description=f"There's a {direction} correlation ({correlation:.2f}) between your daily water intake and step count.",
                                insight_type="correlation",
                                data_types_used=[DataType.WATER_INTAKE, DataType.STEPS],
                                platforms_used=list(set(m.source_platform for m in water_metrics + step_metrics)),
                                date_range_start=(datetime.utcnow() - timedelta(days=30)).date(),
                                date_range_end=datetime.utcnow().date(),
                                confidence_score=0.7,
                                actionable_recommendations=[
                                    "Consider increasing water intake on high-activity days" if correlation > 0 else "Monitor hydration patterns relative to activity levels",
                                    "Track both metrics together to optimize your health routine"
                                ],
                                supporting_data={
                                    "correlation_coefficient": correlation,
                                    "data_points": len(common_dates),
                                    "water_avg": water_avg,
                                    "steps_avg": steps_avg
                                }
                            )
                            
                            insights.append(insight)
        
        return insights

    async def _generate_goal_insights(self, user_id: int, metrics: List[HealthMetric]) -> List[HealthInsight]:
        """Generate goal-related insights."""
        insights = []
        
        # Check water intake against typical recommendations
        water_metrics = [m for m in metrics if m.data_type == DataType.WATER_INTAKE]
        
        if water_metrics:
            # Group by date
            daily_intake = defaultdict(float)
            for metric in water_metrics:
                date_key = metric.timestamp.date()
                daily_intake[date_key] += metric.value
            
            if daily_intake:
                avg_daily_intake = mean(daily_intake.values())
                recommended_intake = 2000  # 2L in mL
                
                if avg_daily_intake < recommended_intake * 0.8:
                    insight = HealthInsight(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        title="Hydration Below Recommended Levels",
                        description=f"Your average daily water intake ({avg_daily_intake:.0f}mL) is below the recommended 2000mL.",
                        insight_type="goal_gap",
                        data_types_used=[DataType.WATER_INTAKE],
                        platforms_used=list(set(m.source_platform for m in water_metrics)),
                        date_range_start=(datetime.utcnow() - timedelta(days=30)).date(),
                        date_range_end=datetime.utcnow().date(),
                        confidence_score=0.9,
                        actionable_recommendations=[
                            "Set a daily water intake goal of 2000mL",
                            "Use reminders to drink water throughout the day",
                            "Keep a water bottle visible as a visual reminder"
                        ],
                        supporting_data={
                            "current_avg": avg_daily_intake,
                            "recommended": recommended_intake,
                            "gap_percent": ((recommended_intake - avg_daily_intake) / recommended_intake) * 100
                        }
                    )
                    
                    insights.append(insight)
        
        return insights

    async def get_user_insights(
        self,
        user_id: int,
        filter_data: Optional[HealthInsightFilter] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[HealthInsight], int]:
        """Get health insights for a user."""
        insights = await self._load_data(self.insights_file)
        user_insights = [HealthInsight(**i) for i in insights if i['user_id'] == user_id]
        
        # Apply filters
        if filter_data:
            if filter_data.insight_types:
                user_insights = [i for i in user_insights if i.insight_type in filter_data.insight_types]
            if filter_data.data_types:
                user_insights = [i for i in user_insights if any(dt in i.data_types_used for dt in filter_data.data_types)]
            if filter_data.platforms:
                user_insights = [i for i in user_insights if any(p in i.platforms_used for p in filter_data.platforms)]
            if filter_data.min_confidence:
                user_insights = [i for i in user_insights if i.confidence_score >= filter_data.min_confidence]
            if filter_data.viewed_only:
                user_insights = [i for i in user_insights if i.viewed_at]
            if filter_data.active_only:
                user_insights = [i for i in user_insights if i.is_active]
            if filter_data.date_from:
                user_insights = [i for i in user_insights if i.date_range_start >= filter_data.date_from]
            if filter_data.date_to:
                user_insights = [i for i in user_insights if i.date_range_end <= filter_data.date_to]
        
        # Sort by generation date (newest first)
        user_insights.sort(key=lambda i: i.generated_at, reverse=True)
        
        total = len(user_insights)
        paginated_insights = user_insights[skip:skip + limit]
        
        return paginated_insights, total

    async def provide_insight_feedback(
        self,
        insight_id: str,
        user_id: int,
        feedback: HealthInsightFeedback
    ) -> Optional[HealthInsight]:
        """Provide feedback on a health insight."""
        insights = await self._load_data(self.insights_file)
        insight_index = next((i for i, insight in enumerate(insights) if insight['id'] == insight_id and insight['user_id'] == user_id), None)
        
        if insight_index is None:
            return None
        
        insights[insight_index].update({
            "user_rating": feedback.user_rating,
            "user_feedback": feedback.user_feedback,
            "viewed_at": datetime.utcnow().isoformat()
        })
        
        await self._save_data(self.insights_file, insights)
        
        logger.info(f"Recorded feedback for insight {insight_id}")
        return HealthInsight(**insights[insight_index])


# Create global instance
health_integration_service = HealthIntegrationService() 