import json
import logging
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
from collections import Counter, defaultdict
import calendar
from itertools import groupby
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, cast, Date, case

from app.models.analytics import UserAnalytics, GlobalAnalytics, ProgressAnalytics, ProgressDataPoint, BrandAnalytics, GlobalStats, ProgressOverTime, TimeSeriesAnalytics, TimeSeriesDataPoint
from app.models.water import WaterData, WaterLog
from app.models.user import User
from app.schemas.analytics import UserStats, TimeSeriesData, TimePeriod, LeaderboardEntry, WaterConsumptionAnalytics, DailyWaterConsumption, LeaderboardType
from app.services.data_service import data_service
from app.services.user_service import user_service
from app.core.cache import timed_lru_cache
from app.db import models as db_models

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        self.water_logs_file = Path(__file__).parent.parent / "data" / "user_water_logs.json"

    async def _read_data(self, file_path: Path) -> List[Dict]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    async def get_user_analytics(self, user_id: int) -> Optional[UserAnalytics]:
        """Generate personalized analytics for a user for the last 30 days."""
        all_logs = await self._read_data(self.water_logs_file)
        user_logs = [log for log in all_logs if log.get("user_id") == user_id]

        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=30)

        recent_logs = [
            log for log in user_logs 
            if start_date <= datetime.fromisoformat(log["date"]).date() <= end_date
        ]

        if not recent_logs:
            return None # Or return a default analytics object

        total_logs = len(recent_logs)
        total_volume = sum(log.get("volume", 0) for log in recent_logs)
        
        # Calculate average daily volume
        num_days = (end_date - start_date).days + 1
        average_daily_volume = total_volume / num_days if num_days > 0 else 0

        # Most frequent brand
        brand_counter = Counter(log.get("brand") for log in recent_logs if log.get("brand"))
        most_frequent_brand = brand_counter.most_common(1)[0][0] if brand_counter else None

        # Packaging breakdown
        all_water_products = await data_service.get_all_water_data()
        water_products_map = {
            product.id: product for product in all_water_products
        }
        
        packaging_types = []
        for log in recent_logs:
            product = water_products_map.get(log.get("water_id"))
            if product and product.packaging:
                packaging_types.append(product.packaging)
        
        packaging_breakdown = Counter(packaging_types)

        # Consumption heatmap
        heatmap = {
            "monday": [0]*24, "tuesday": [0]*24, "wednesday": [0]*24,
            "thursday": [0]*24, "friday": [0]*24, "saturday": [0]*24, "sunday": [0]*24
        }
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for log in recent_logs:
            log_date = datetime.fromisoformat(log["date"])
            day_of_week = days[log_date.weekday()]
            hour_of_day = log_date.hour
            heatmap[day_of_week][hour_of_day] += 1

        return UserAnalytics(
            user_id=user_id,
            period_start_date=start_date,
            period_end_date=end_date,
            total_logs=total_logs,
            total_volume=round(total_volume, 2),
            average_daily_volume=round(average_daily_volume, 2),
            most_frequent_brand=most_frequent_brand,
            packaging_breakdown=dict(packaging_breakdown),
            consumption_heatmap=heatmap
        )

    async def get_brand_specific_user_analytics(self, user_id: int, brand_name: str) -> Optional[UserAnalytics]:
        """Generate personalized analytics for a user for a specific brand."""
        all_logs = await self._read_data(self.water_logs_file)
        
        # Filter logs for the specific user AND brand
        brand_name_lower = brand_name.lower()
        user_logs = [
            log for log in all_logs 
            if log.get("user_id") == user_id and log.get("brand", "").lower() == brand_name_lower
        ]

        if not user_logs:
            return None

        # Analytics calculations are now performed on the pre-filtered logs
        end_date = datetime.utcnow().date()
        start_date = min(datetime.fromisoformat(log["date"]).date() for log in user_logs)

        total_logs = len(user_logs)
        total_volume = sum(log.get("volume", 0) for log in user_logs)
        
        num_days = (end_date - start_date).days + 1
        average_daily_volume = total_volume / num_days if num_days > 0 else 0

        # Most frequent brand will be the one we are filtering by
        most_frequent_brand = brand_name

        # Packaging breakdown for the specific brand
        all_water_products = await data_service.get_all_water_data()
        water_products_map = {p.id: p for p in all_water_products}
        
        packaging_types = [
            water_products_map[log["water_id"]].packaging
            for log in user_logs if log.get("water_id") in water_products_map
        ]
        packaging_breakdown = Counter(packaging_types)

        # Heatmap for the specific brand
        heatmap = {day: [0]*24 for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]}
        days = list(heatmap.keys())
        for log in user_logs:
            log_date = datetime.fromisoformat(log["date"])
            heatmap[days[log_date.weekday()]][log_date.hour] += 1

        return UserAnalytics(
            user_id=user_id,
            period_start_date=start_date,
            period_end_date=end_date,
            total_logs=total_logs,
            total_volume=round(total_volume, 2),
            average_daily_volume=round(average_daily_volume, 2),
            most_frequent_brand=most_frequent_brand,
            packaging_breakdown=dict(packaging_breakdown),
            consumption_heatmap=heatmap
        )

    @timed_lru_cache(seconds=3600) # Cache for 1 hour
    async def get_global_analytics(self) -> GlobalAnalytics:
        """Calculate and return aggregated, anonymous statistics for the entire platform."""
        logger.info("Cache miss. Calculating global analytics from scratch.")
        all_users = await user_service.get_all_users(limit=10000) # A high limit to get all users
        all_logs = await self._read_data(self.water_logs_file)

        total_users = len(all_users)
        total_water_logs = len(all_logs)
        total_volume_logged = sum(log.get("volume", 0) for log in all_logs)

        # Most popular brand
        brand_counter = Counter(log.get("brand") for log in all_logs if log.get("brand"))
        most_popular_brand = brand_counter.most_common(1)[0][0] if brand_counter else None

        # Packaging breakdown
        all_water_products = await data_service.get_all_water_data()
        water_products_map = {
            product.id: product for product in all_water_products
        }
        
        packaging_types = []
        for log in all_logs:
            product = water_products_map.get(log.get("water_id"))
            if product and product.packaging:
                packaging_types.append(product.packaging)
        
        packaging_breakdown = Counter(packaging_types)

        return GlobalAnalytics(
            total_users=total_users,
            total_water_logs=total_water_logs,
            total_volume_logged=round(total_volume_logged, 2),
            most_popular_brand=most_popular_brand,
            platform_wide_packaging_breakdown=dict(packaging_breakdown)
        )

    async def get_progress_over_time(self, user_id: int, granularity: str = "weekly") -> Optional[ProgressAnalytics]:
        """Calculate a user's average daily consumption over time."""
        all_logs = await self._read_data(self.water_logs_file)
        user_logs = [log for log in all_logs if log.get("user_id") == user_id]

        if not user_logs:
            return None

        # Convert string dates to datetime objects
        for log in user_logs:
            log['date_obj'] = datetime.fromisoformat(log['date'])
        
        user_logs.sort(key=lambda x: x['date_obj'])
        
        data_points = []
        
        if granularity == "weekly":
            # Group by week number
            grouper = lambda log: log['date_obj'].isocalendar()[1]
            for week_num, group in groupby(user_logs, key=grouper):
                week_logs = list(group)
                start_of_week = week_logs[0]['date_obj'].date() - timedelta(days=week_logs[0]['date_obj'].weekday())
                end_of_week = start_of_week + timedelta(days=6)
                
                total_volume = sum(log.get("volume", 0) for log in week_logs)
                avg_daily_volume = total_volume / 7
                
                data_points.append(
                    ProgressDataPoint(
                        period_start=start_of_week,
                        period_end=end_of_week,
                        value=round(avg_daily_volume, 2)
                    )
                )

        elif granularity == "monthly":
            # Group by month and year
            grouper = lambda log: (log['date_obj'].year, log['date_obj'].month)
            for (year, month), group in groupby(user_logs, key=grouper):
                month_logs = list(group)
                
                _, num_days_in_month = calendar.monthrange(year, month)
                start_of_month = date(year, month, 1)
                end_of_month = date(year, month, num_days_in_month)

                total_volume = sum(log.get("volume", 0) for log in month_logs)
                avg_daily_volume = total_volume / num_days_in_month
                
                data_points.append(
                    ProgressDataPoint(
                        period_start=start_of_month,
                        period_end=end_of_month,
                        value=round(avg_daily_volume, 2)
                    )
                )

        return ProgressAnalytics(
            user_id=user_id,
            time_granularity=granularity,
            data_points=data_points
        )

    def get_consumption_heatmap(self, db: Session, user_id: int) -> dict:
        """Generates a heatmap of water consumption for the last year."""
        today = datetime.utcnow().date()
        
        results = db.query(
            func.date(db_models.WaterLog.date),
            func.sum(db_models.WaterLog.volume)
        ).filter(
            db_models.WaterLog.user_id == user_id,
            db_models.WaterLog.date >= today - timedelta(days=365)
        ).group_by(
            func.date(db_models.WaterLog.date)
        ).all()

        return {str(date): volume for date, volume in results}

    def get_brand_analytics_for_user(self, db: Session, user_id: int, brand_name: str) -> BrandAnalytics:
        """Calculates analytics for a specific brand for a user."""
        query = db.query(
            func.sum(db_models.WaterLog.volume),
            func.count(db_models.WaterLog.id),
            func.min(db_models.WaterLog.date),
            func.max(db_models.WaterLog.date)
        ).join(db_models.WaterData).filter(
            db_models.WaterLog.user_id == user_id,
            db_models.WaterData.brand_name == brand_name
        )
        
        total_volume, total_logs, first_date, last_date = query.one()

        if not total_logs:
            return None

        return BrandAnalytics(
            brand_name=brand_name,
            total_volume_ml=total_volume or 0,
            total_logs=total_logs or 0,
            first_logged_date=str(first_date) if first_date else "N/A",
            last_logged_date=str(last_date) if last_date else "N/A",
        )

    def get_global_stats(self, db: Session) -> GlobalStats:
        """Calculates anonymous, global statistics."""
        total_users = db.query(func.count(db_models.User.id)).scalar()
        total_logs = db.query(func.count(db_models.WaterLog.id)).scalar()
        total_volume = db.query(func.sum(db_models.WaterLog.volume)).scalar() or 0

        most_popular_brand_query = db.query(
            db_models.WaterData.brand_name,
            func.count(db_models.WaterLog.id).label('log_count')
        ).join(db_models.WaterLog).group_by(db_models.WaterData.brand_name).order_by(desc('log_count')).first()
        
        most_popular_brand = most_popular_brand_query[0] if most_popular_brand_query else "N/A"

        # This is a simplified average daily intake calculation
        total_days_logging = db.query(func.count(func.distinct(func.date(db_models.WaterLog.date)))).scalar() or 1
        average_daily_intake = total_volume / total_days_logging if total_days_logging > 0 else 0

        return GlobalStats(
            total_users=total_users,
            total_water_logs=total_logs,
            total_volume_logged_ml=total_volume,
            most_popular_brand=most_popular_brand,
            average_daily_intake_ml=average_daily_intake
        )

    def get_progress_over_time(self, db: Session, user_id: int, period: str = "weekly") -> ProgressOverTime:
        """Calculates a user's consumption progress over a given period."""
        # This is a placeholder for a more complex implementation
        # that would handle different time periods and data aggregation.
        data = self.get_consumption_heatmap(db, user_id)
        return ProgressOverTime(period=period, data=data)

    def get_water_intake_timeseries(
        self,
        db: Session,
        user_id: int,
        start_date: date,
        end_date: date,
        granularity: str = "daily"
    ) -> TimeSeriesAnalytics:
        """
        Get a user's water intake as a time series.
        Granularity can be 'daily', 'weekly', or 'monthly'.
        """
        query = db.query(
            cast(db_models.WaterLog.date, Date).label("log_date"),
            func.sum(db_models.WaterLog.volume).label("total_volume")
        ).filter(
            db_models.WaterLog.user_id == user_id,
            db_models.WaterLog.date >= start_date,
            db_models.WaterLog.date < end_date + timedelta(days=1)
        ).group_by("log_date").order_by("log_date")

        daily_data = {row.log_date: row.total_volume for row in query.all()}
        
        data_points = []
        current_date = start_date
        
        if granularity == "daily":
            while current_date <= end_date:
                data_points.append(TimeSeriesDataPoint(
                    timestamp=current_date,
                    value=daily_data.get(current_date, 0.0)
                ))
                current_date += timedelta(days=1)
        
        elif granularity == "weekly":
            while current_date <= end_date:
                week_end = current_date + timedelta(days=6)
                week_volume = sum(
                    daily_data.get(d, 0.0)
                    for d in daily_data
                    if current_date <= d <= week_end
                )
                data_points.append(TimeSeriesDataPoint(timestamp=current_date, value=week_volume))
                current_date += timedelta(days=7)

        elif granularity == "monthly":
            while current_date <= end_date:
                month_volume = sum(
                    daily_data.get(d, 0.0)
                    for d in daily_data
                    if d.year == current_date.year and d.month == current_date.month
                )
                data_points.append(TimeSeriesDataPoint(timestamp=current_date.replace(day=1), value=month_volume))
                
                # Move to the first day of the next month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1, day=1)
        
        return TimeSeriesAnalytics(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity,
            data_points=data_points
        )

    def get_user_stats(self, db: Session, *, user_id: int) -> UserStats:
        """
        Gathers a comprehensive set of statistics for a single user.
        """
        total_logs = db.query(WaterLog).filter(WaterLog.user_id == user_id).count()
        total_volume = db.query(func.sum(WaterLog.volume_ml)).filter(WaterLog.user_id == user_id).scalar() or 0
        
        first_log = db.query(WaterLog).filter(WaterLog.user_id == user_id).order_by(WaterLog.timestamp.asc()).first()
        last_log = db.query(WaterLog).filter(WaterLog.user_id == user_id).order_by(WaterLog.timestamp.desc()).first()
        
        days_tracking = (last_log.timestamp.date() - first_log.timestamp.date()).days + 1 if first_log and last_log else 0
        average_daily_volume = total_volume / days_tracking if days_tracking > 0 else 0

        return UserStats(
            total_logs=total_logs,
            total_volume_ml=total_volume,
            average_daily_volume_ml=average_daily_volume,
            tracking_start_date=first_log.timestamp if first_log else None
        )

    def get_user_intake_timeseries(self, db: Session, *, user_id: int, period: TimePeriod) -> List[TimeSeriesData]:
        """
        Generates time series data for a user's water intake, grouped by day, week, or month.
        """
        if period == TimePeriod.DAY:
            date_trunc = func.date(WaterLog.timestamp)
        elif period == TimePeriod.WEEK:
            # Adjust for SQLite's lack of a specific date_trunc for week
            date_trunc = func.strftime('%Y-%W', WaterLog.timestamp)
        else: # MONTH
            date_trunc = func.strftime('%Y-%m', WaterLog.timestamp)

        results = (
            db.query(
                date_trunc.label("period_start"),
                func.sum(WaterLog.volume_ml).label("total_volume")
            )
            .filter(WaterLog.user_id == user_id)
            .group_by("period_start")
            .order_by("period_start")
            .all()
        )
        return [TimeSeriesData(period_start=row.period_start, total_volume=row.total_volume) for row in results]

    def get_leaderboard(
        self, db: Session, *, leaderboard_type: LeaderboardType, period: TimePeriod, limit: int = 10
    ) -> List[LeaderboardEntry]:
        """
        Retrieves the public leaderboard, ranking users by water intake or streak.
        """
        if leaderboard_type == LeaderboardType.STREAK:
            # Rank by longest_streak in UserProfile
            query = (
                db.query(
                    db_models.User.id,
                    db_models.User.username,
                    db_models.UserProfile.longest_streak,
                )
                .join(db_models.UserProfile, db_models.User.id == db_models.UserProfile.user_id)
                .order_by(desc(db_models.UserProfile.longest_streak))
                .limit(limit)
            )
            results = query.all()
            return [
                LeaderboardEntry(rank=i + 1, user_id=r.id, username=r.username, value=r.longest_streak, streak=r.longest_streak)
                for i, r in enumerate(results)
            ]

        # Default to consumption leaderboard
        start_date = self._get_start_date_for_period(period)
        
        query = (
            db.query(
                db_models.WaterLog.user_id,
                db_models.User.username,
                func.sum(db_models.WaterLog.volume).label("total_volume"),
            )
            .join(db_models.User, db_models.WaterLog.user_id == db_models.User.id)
            .filter(db_models.WaterLog.date >= start_date)
            .group_by(db_models.WaterLog.user_id, db_models.User.username)
            .order_by(desc("total_volume"))
            .limit(limit)
        )
        
        results = query.all()
        return [
            LeaderboardEntry(rank=i + 1, user_id=r.user_id, username=r.username, value=r.total_volume)
            for i, r in enumerate(results)
        ]

    def get_water_consumption_analytics(self, db: Session, user_id: int, start_date: date, end_date: date) -> WaterConsumptionAnalytics:
        """
        Calculates water consumption analytics for a given user and date range.
        """
        
        # Query to get daily consumption
        daily_consumption_query = (
            db.query(
                func.date(db_models.WaterLog.date).label("consumption_date"),
                func.sum(db_models.WaterLog.volume).label("total_volume"),
            )
            .filter(db_models.WaterLog.user_id == user_id)
            .filter(func.date(db_models.WaterLog.date) >= start_date)
            .filter(func.date(db_models.WaterLog.date) <= end_date)
            .group_by("consumption_date")
            .order_by("consumption_date")
        )

        daily_results = daily_consumption_query.all()

        daily_consumption_data = [
            DailyWaterConsumption(date=row.consumption_date, total_consumption=row.total_volume)
            for row in daily_results
        ]

        total_consumption = sum(item.total_consumption for item in daily_consumption_data)
        
        num_days = (end_date - start_date).days + 1
        average_daily_consumption = total_consumption / num_days if num_days > 0 else 0

        return WaterConsumptionAnalytics(
            total_consumption=total_consumption,
            average_daily_consumption=average_daily_consumption,
            daily_consumption=daily_consumption_data,
        )

analytics_service = AnalyticsService() 