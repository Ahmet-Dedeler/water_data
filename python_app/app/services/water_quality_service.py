from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, case
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import statistics
from collections import defaultdict

from app.models.water_quality import (
    WaterSource, WaterQualityTest, ContaminationReport, WaterQualityAlert,
    WaterFilterMaintenance, WaterQualityPreference, WaterSourceType,
    WaterQualityRating, ContaminantType
)
from app.schemas.water_quality import (
    WaterSourceCreate, WaterSourceUpdate, WaterQualityTestCreate, WaterQualityTestUpdate,
    ContaminationReportCreate, ContaminationReportUpdate, WaterQualityAlertCreate,
    WaterFilterMaintenanceCreate, WaterFilterMaintenanceUpdate,
    WaterQualityPreferencesCreate, WaterQualityPreferencesUpdate,
    WaterQualityAnalytics, WaterQualityTrend, WaterQualitySummary
)

class WaterQualityService:
    def __init__(self, db: Session):
        self.db = db

    # Water Source Management
    def create_water_source(self, user_id: int, source_data: WaterSourceCreate) -> WaterSource:
        """Create a new water source for a user"""
        # If this is set as primary, unset other primary sources
        if source_data.is_primary:
            self.db.query(WaterSource).filter(
                and_(WaterSource.user_id == user_id, WaterSource.is_primary == True)
            ).update({"is_primary": False})

        source = WaterSource(
            user_id=user_id,
            **source_data.dict()
        )
        
        # Set next test due date based on source type
        if source.type in [WaterSourceType.TAP, WaterSourceType.WELL]:
            source.next_test_due = datetime.utcnow() + timedelta(days=90)
        elif source.type == WaterSourceType.FILTERED:
            source.next_test_due = datetime.utcnow() + timedelta(days=180)
        else:
            source.next_test_due = datetime.utcnow() + timedelta(days=365)

        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source

    def get_user_water_sources(self, user_id: int, active_only: bool = True) -> List[WaterSource]:
        """Get all water sources for a user"""
        query = self.db.query(WaterSource).filter(WaterSource.user_id == user_id)
        if active_only:
            query = query.filter(WaterSource.is_active == True)
        return query.order_by(WaterSource.is_primary.desc(), WaterSource.created_at.desc()).all()

    def get_water_source(self, user_id: int, source_id: int) -> Optional[WaterSource]:
        """Get a specific water source"""
        return self.db.query(WaterSource).filter(
            and_(WaterSource.id == source_id, WaterSource.user_id == user_id)
        ).first()

    def update_water_source(self, user_id: int, source_id: int, update_data: WaterSourceUpdate) -> Optional[WaterSource]:
        """Update a water source"""
        source = self.get_water_source(user_id, source_id)
        if not source:
            return None

        update_dict = update_data.dict(exclude_unset=True)
        
        # Handle primary source logic
        if update_dict.get('is_primary'):
            self.db.query(WaterSource).filter(
                and_(WaterSource.user_id == user_id, WaterSource.id != source_id)
            ).update({"is_primary": False})

        for field, value in update_dict.items():
            setattr(source, field, value)

        source.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(source)
        return source

    def delete_water_source(self, user_id: int, source_id: int) -> bool:
        """Delete a water source"""
        source = self.get_water_source(user_id, source_id)
        if not source:
            return False

        source.is_active = False
        source.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    # Water Quality Testing
    def create_quality_test(self, user_id: int, test_data: WaterQualityTestCreate) -> WaterQualityTest:
        """Create a new water quality test"""
        # Verify source belongs to user
        source = self.get_water_source(user_id, test_data.source_id)
        if not source:
            raise ValueError("Water source not found")

        test = WaterQualityTest(
            user_id=user_id,
            **test_data.dict()
        )

        self.db.add(test)
        
        # Update source with latest test data
        source.last_tested = test.test_date
        source.quality_rating = test.overall_rating
        if test.ph_level:
            source.ph_level = test.ph_level
        if test.tds_level:
            source.tds_level = test.tds_level
        if test.hardness:
            source.hardness = test.hardness

        # Set next test due date
        source.next_test_due = self._calculate_next_test_date(source.type, test.overall_rating)
        
        self.db.commit()
        self.db.refresh(test)
        
        # Check for quality alerts
        self._check_quality_alerts(user_id, source, test)
        
        return test

    def get_quality_tests(self, user_id: int, source_id: Optional[int] = None) -> List[WaterQualityTest]:
        """Get quality tests for user or specific source"""
        query = self.db.query(WaterQualityTest).filter(WaterQualityTest.user_id == user_id)
        if source_id:
            query = query.filter(WaterQualityTest.source_id == source_id)
        return query.order_by(WaterQualityTest.test_date.desc()).all()

    def update_quality_test(self, user_id: int, test_id: int, update_data: WaterQualityTestUpdate) -> Optional[WaterQualityTest]:
        """Update a quality test"""
        test = self.db.query(WaterQualityTest).filter(
            and_(WaterQualityTest.id == test_id, WaterQualityTest.user_id == user_id)
        ).first()
        
        if not test:
            return None

        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(test, field, value)

        self.db.commit()
        self.db.refresh(test)
        return test

    # Contamination Reporting
    def create_contamination_report(self, user_id: int, report_data: ContaminationReportCreate) -> ContaminationReport:
        """Create a contamination report"""
        source = self.get_water_source(user_id, report_data.source_id)
        if not source:
            raise ValueError("Water source not found")

        report = ContaminationReport(
            user_id=user_id,
            **report_data.dict()
        )

        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)

        # Create critical alert for high severity contamination
        if report.severity_level >= 4:
            self._create_contamination_alert(user_id, source, report)

        return report

    def get_contamination_reports(self, user_id: int, source_id: Optional[int] = None) -> List[ContaminationReport]:
        """Get contamination reports"""
        query = self.db.query(ContaminationReport).filter(ContaminationReport.user_id == user_id)
        if source_id:
            query = query.filter(ContaminationReport.source_id == source_id)
        return query.order_by(ContaminationReport.created_at.desc()).all()

    def update_contamination_report(self, user_id: int, report_id: int, update_data: ContaminationReportUpdate) -> Optional[ContaminationReport]:
        """Update a contamination report"""
        report = self.db.query(ContaminationReport).filter(
            and_(ContaminationReport.id == report_id, ContaminationReport.user_id == user_id)
        ).first()
        
        if not report:
            return None

        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(report, field, value)

        if update_dict.get('resolved') and not report.resolution_date:
            report.resolution_date = datetime.utcnow()

        report.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(report)
        return report

    # Water Quality Alerts
    def create_alert(self, user_id: int, alert_data: WaterQualityAlertCreate) -> WaterQualityAlert:
        """Create a water quality alert"""
        alert = WaterQualityAlert(
            user_id=user_id,
            **alert_data.dict()
        )

        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def get_user_alerts(self, user_id: int, active_only: bool = True) -> List[WaterQualityAlert]:
        """Get alerts for a user"""
        query = self.db.query(WaterQualityAlert).filter(WaterQualityAlert.user_id == user_id)
        if active_only:
            query = query.filter(WaterQualityAlert.is_active == True)
        return query.order_by(WaterQualityAlert.created_at.desc()).all()

    def acknowledge_alert(self, user_id: int, alert_id: int) -> Optional[WaterQualityAlert]:
        """Acknowledge an alert"""
        alert = self.db.query(WaterQualityAlert).filter(
            and_(WaterQualityAlert.id == alert_id, WaterQualityAlert.user_id == user_id)
        ).first()
        
        if not alert:
            return None

        alert.acknowledged = True
        alert.acknowledged_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def resolve_alert(self, user_id: int, alert_id: int) -> Optional[WaterQualityAlert]:
        """Resolve an alert"""
        alert = self.db.query(WaterQualityAlert).filter(
            and_(WaterQualityAlert.id == alert_id, WaterQualityAlert.user_id == user_id)
        ).first()
        
        if not alert:
            return None

        alert.resolved = True
        alert.resolved_at = datetime.utcnow()
        alert.is_active = False
        self.db.commit()
        self.db.refresh(alert)
        return alert

    # Filter Maintenance
    def create_filter_maintenance(self, user_id: int, maintenance_data: WaterFilterMaintenanceCreate) -> WaterFilterMaintenance:
        """Create filter maintenance record"""
        source = self.get_water_source(user_id, maintenance_data.source_id)
        if not source:
            raise ValueError("Water source not found")

        maintenance = WaterFilterMaintenance(
            user_id=user_id,
            **maintenance_data.dict()
        )
        
        # Calculate next maintenance due
        maintenance.next_maintenance_due = maintenance.installation_date + timedelta(
            days=maintenance.maintenance_frequency_days
        )

        self.db.add(maintenance)
        self.db.commit()
        self.db.refresh(maintenance)
        return maintenance

    def get_filter_maintenance(self, user_id: int, source_id: Optional[int] = None) -> List[WaterFilterMaintenance]:
        """Get filter maintenance records"""
        query = self.db.query(WaterFilterMaintenance).filter(WaterFilterMaintenance.user_id == user_id)
        if source_id:
            query = query.filter(WaterFilterMaintenance.source_id == source_id)
        return query.order_by(WaterFilterMaintenance.next_maintenance_due.asc()).all()

    def update_filter_maintenance(self, user_id: int, maintenance_id: int, update_data: WaterFilterMaintenanceUpdate) -> Optional[WaterFilterMaintenance]:
        """Update filter maintenance record"""
        maintenance = self.db.query(WaterFilterMaintenance).filter(
            and_(WaterFilterMaintenance.id == maintenance_id, WaterFilterMaintenance.user_id == user_id)
        ).first()
        
        if not maintenance:
            return None

        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(maintenance, field, value)

        # Recalculate next maintenance due if maintenance was performed
        if update_dict.get('last_maintenance'):
            maintenance.next_maintenance_due = update_dict['last_maintenance'] + timedelta(
                days=maintenance.maintenance_frequency_days
            )
            maintenance.filter_life_percentage = 100.0  # Reset filter life

        maintenance.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(maintenance)
        return maintenance

    # Water Quality Preferences
    def get_or_create_preferences(self, user_id: int) -> WaterQualityPreference:
        """Get or create user preferences"""
        preferences = self.db.query(WaterQualityPreference).filter(
            WaterQualityPreference.user_id == user_id
        ).first()
        
        if not preferences:
            preferences = WaterQualityPreference(user_id=user_id)
            self.db.add(preferences)
            self.db.commit()
            self.db.refresh(preferences)
        
        return preferences

    def update_preferences(self, user_id: int, update_data: WaterQualityPreferencesUpdate) -> WaterQualityPreference:
        """Update user preferences"""
        preferences = self.get_or_create_preferences(user_id)
        
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(preferences, field, value)

        preferences.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(preferences)
        return preferences

    # Analytics and Reporting
    def get_quality_analytics(self, user_id: int) -> WaterQualityAnalytics:
        """Get water quality analytics for user"""
        sources = self.get_user_water_sources(user_id, active_only=False)
        active_sources = [s for s in sources if s.is_active]
        
        tests = self.get_quality_tests(user_id)
        contamination_reports = self.get_contamination_reports(user_id)
        alerts = self.get_user_alerts(user_id, active_only=False)
        filters = self.get_filter_maintenance(user_id)

        # Calculate average quality rating
        if tests:
            rating_values = {"excellent": 5, "good": 4, "fair": 3, "poor": 2, "unknown": 1}
            avg_rating_value = statistics.mean([rating_values.get(test.overall_rating.value, 1) for test in tests])
            avg_rating = max(rating_values.keys(), key=lambda k: abs(rating_values[k] - avg_rating_value))
        else:
            avg_rating = None

        # Count overdue tests
        now = datetime.utcnow()
        overdue_tests = len([s for s in active_sources if s.next_test_due and s.next_test_due < now])

        return WaterQualityAnalytics(
            total_sources=len(sources),
            active_sources=len(active_sources),
            tests_conducted=len(tests),
            average_quality_rating=avg_rating,
            contamination_reports=len(contamination_reports),
            resolved_contaminations=len([r for r in contamination_reports if r.resolved]),
            filters_maintained=len([f for f in filters if f.last_maintenance]),
            overdue_tests=overdue_tests,
            active_alerts=len([a for a in alerts if a.is_active])
        )

    def get_quality_trends(self, user_id: int, days: int = 30) -> List[WaterQualityTrend]:
        """Get water quality trends over time"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        tests = self.db.query(WaterQualityTest).filter(
            and_(
                WaterQualityTest.user_id == user_id,
                WaterQualityTest.test_date >= start_date
            )
        ).order_by(WaterQualityTest.test_date.asc()).all()

        trends = []
        for test in tests:
            trends.append(WaterQualityTrend(
                date=test.test_date,
                ph_level=test.ph_level,
                tds_level=test.tds_level,
                safety_score=test.safety_score,
                quality_rating=test.overall_rating.value
            ))

        return trends

    def get_quality_summary(self, user_id: int) -> WaterQualitySummary:
        """Get comprehensive quality summary"""
        analytics = self.get_quality_analytics(user_id)
        trends = self.get_quality_trends(user_id)
        active_alerts = self.get_user_alerts(user_id, active_only=True)
        
        # Get sources with upcoming tests
        now = datetime.utcnow()
        upcoming_test_date = now + timedelta(days=30)
        sources = self.get_user_water_sources(user_id)
        upcoming_tests = [
            s for s in sources 
            if s.next_test_due and now <= s.next_test_due <= upcoming_test_date
        ]
        
        # Get filters needing maintenance
        filters = self.get_filter_maintenance(user_id)
        maintenance_due = [
            f for f in filters 
            if f.next_maintenance_due <= upcoming_test_date and f.is_active
        ]

        return WaterQualitySummary(
            user_id=user_id,
            analytics=analytics,
            recent_trends=trends,
            active_alerts=active_alerts,
            upcoming_tests=upcoming_tests,
            filter_maintenance_due=maintenance_due
        )

    # Helper Methods
    def _calculate_next_test_date(self, source_type: WaterSourceType, quality_rating: WaterQualityRating) -> datetime:
        """Calculate next test due date based on source type and quality"""
        base_days = {
            WaterSourceType.TAP: 90,
            WaterSourceType.WELL: 90,
            WaterSourceType.FILTERED: 180,
            WaterSourceType.BOTTLED: 365,
            WaterSourceType.SPRING: 180,
            WaterSourceType.DISTILLED: 365,
            WaterSourceType.SPARKLING: 365,
            WaterSourceType.ALKALINE: 180,
            WaterSourceType.REVERSE_OSMOSIS: 180,
            WaterSourceType.UV_TREATED: 120
        }
        
        days = base_days.get(source_type, 180)
        
        # Adjust based on quality rating
        if quality_rating == WaterQualityRating.POOR:
            days = days // 2  # Test more frequently for poor quality
        elif quality_rating == WaterQualityRating.EXCELLENT:
            days = int(days * 1.5)  # Test less frequently for excellent quality
        
        return datetime.utcnow() + timedelta(days=days)

    def _check_quality_alerts(self, user_id: int, source: WaterSource, test: WaterQualityTest):
        """Check if test results warrant alerts"""
        preferences = self.get_or_create_preferences(user_id)
        
        alerts_to_create = []
        
        # pH level alerts
        if test.ph_level:
            if test.ph_level < preferences.preferred_ph_min or test.ph_level > preferences.preferred_ph_max:
                alerts_to_create.append({
                    "alert_type": "ph_out_of_range",
                    "severity": "medium",
                    "title": "pH Level Out of Preferred Range",
                    "message": f"Water pH level ({test.ph_level}) is outside your preferred range ({preferences.preferred_ph_min}-{preferences.preferred_ph_max})",
                    "source_id": source.id,
                    "trigger_data": {"ph_level": test.ph_level, "test_id": test.id}
                })

        # TDS level alerts
        if test.tds_level and test.tds_level > preferences.preferred_tds_max:
            alerts_to_create.append({
                "alert_type": "high_tds",
                "severity": "medium",
                "title": "High TDS Level Detected",
                "message": f"Total Dissolved Solids ({test.tds_level} ppm) exceeds your preferred maximum ({preferences.preferred_tds_max} ppm)",
                "source_id": source.id,
                "trigger_data": {"tds_level": test.tds_level, "test_id": test.id}
            })

        # Contamination alerts
        if test.lead_level and test.lead_level > 15:  # EPA action level
            alerts_to_create.append({
                "alert_type": "lead_contamination",
                "severity": "critical",
                "title": "Lead Contamination Detected",
                "message": f"Lead level ({test.lead_level} µg/L) exceeds EPA action level (15 µg/L)",
                "source_id": source.id,
                "trigger_data": {"lead_level": test.lead_level, "test_id": test.id}
            })

        if test.bacteria_count and test.bacteria_count > 0:
            alerts_to_create.append({
                "alert_type": "bacteria_detected",
                "severity": "high",
                "title": "Bacteria Detected in Water",
                "message": f"Bacteria count: {test.bacteria_count} CFU/mL",
                "source_id": source.id,
                "trigger_data": {"bacteria_count": test.bacteria_count, "test_id": test.id}
            })

        # Create alerts
        for alert_data in alerts_to_create:
            self.create_alert(user_id, WaterQualityAlertCreate(**alert_data))

    def _create_contamination_alert(self, user_id: int, source: WaterSource, report: ContaminationReport):
        """Create alert for contamination report"""
        severity_map = {1: "low", 2: "low", 3: "medium", 4: "high", 5: "critical"}
        
        alert_data = WaterQualityAlertCreate(
            alert_type="contamination_report",
            severity=severity_map[report.severity_level],
            title=f"{report.contaminant_type.value.title()} Contamination Reported",
            message=f"Contamination of type {report.contaminant_type.value} reported for {source.name}",
            source_id=source.id,
            trigger_data={"report_id": report.id, "contaminant_type": report.contaminant_type.value}
        )
        
        self.create_alert(user_id, alert_data) 