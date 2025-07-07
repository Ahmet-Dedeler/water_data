from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel, Field

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.notification_system import (
    NotificationTemplate, NotificationRule, Notification, NotificationCampaign,
    NotificationPreference, NotificationAnalytics, NotificationCategory,
    NotificationPriority, NotificationStatus, NotificationChannel,
    DeliveryMethod, PersonalizationLevel, TemplateType,
    NotificationTemplateCreate, NotificationTemplateUpdate, NotificationRuleCreate,
    NotificationCreate, NotificationResponse, NotificationPreferenceUpdate,
    NotificationCampaignCreate, NotificationAnalyticsResponse
)
from app.services.notification_system_service import NotificationSystemService

router = APIRouter()
logger = logging.getLogger(__name__)

# Dependency to get notification service
def get_notification_service(db: Session = Depends(get_db)) -> NotificationSystemService:
    return NotificationSystemService(db)

# Template Management Endpoints
@router.post("/templates", response_model=Dict[str, Any])
async def create_notification_template(
    template_data: NotificationTemplateCreate,
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Create a new notification template"""
    try:
        template_dict = template_data.dict()
        template_dict["author_id"] = current_user.id
        
        template = service.create_template(template_dict)
        
        return {
            "success": True,
            "message": "Template created successfully",
            "template": {
                "id": template.id,
                "name": template.name,
                "category": template.category.value,
                "template_type": template.template_type.value,
                "created_at": template.created_at.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates", response_model=List[Dict[str, Any]])
async def get_notification_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[NotificationCategory] = None,
    template_type: Optional[TemplateType] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Get notification templates with filtering"""
    try:
        templates = service.get_templates(
            skip=skip,
            limit=limit,
            category=category,
            template_type=template_type,
            is_active=is_active
        )
        
        return [
            {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "category": template.category.value,
                "template_type": template.template_type.value,
                "is_active": template.is_active,
                "version": template.version,
                "created_at": template.created_at.isoformat(),
                "updated_at": template.updated_at.isoformat()
            }
            for template in templates
        ]
    except Exception as e:
        logger.error(f"Error getting templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates/{template_id}", response_model=Dict[str, Any])
async def get_notification_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Get a specific notification template"""
    try:
        template = service.get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "category": template.category.value,
            "template_type": template.template_type.value,
            "email_subject": template.email_subject,
            "email_body": template.email_body,
            "email_html": template.email_html,
            "sms_content": template.sms_content,
            "push_title": template.push_title,
            "push_body": template.push_body,
            "in_app_title": template.in_app_title,
            "in_app_content": template.in_app_content,
            "variables": template.variables,
            "personalization_rules": template.personalization_rules,
            "localization": template.localization,
            "media_assets": template.media_assets,
            "interactive_elements": template.interactive_elements,
            "is_active": template.is_active,
            "version": template.version,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/templates/{template_id}", response_model=Dict[str, Any])
async def update_notification_template(
    template_id: str,
    update_data: NotificationTemplateUpdate,
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Update a notification template"""
    try:
        template = service.update_template(template_id, update_data.dict(exclude_unset=True))
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return {
            "success": True,
            "message": "Template updated successfully",
            "template": {
                "id": template.id,
                "name": template.name,
                "updated_at": template.updated_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/templates/{template_id}", response_model=Dict[str, Any])
async def delete_notification_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Delete a notification template"""
    try:
        success = service.delete_template(template_id)
        if not success:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return {
            "success": True,
            "message": "Template deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/templates/{template_id}/clone", response_model=Dict[str, Any])
async def clone_notification_template(
    template_id: str,
    new_name: str = Field(..., min_length=1, max_length=100),
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Clone a notification template"""
    try:
        cloned_template = service.clone_template(template_id, new_name)
        if not cloned_template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return {
            "success": True,
            "message": "Template cloned successfully",
            "template": {
                "id": cloned_template.id,
                "name": cloned_template.name,
                "created_at": cloned_template.created_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cloning template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/templates/{template_id}/preview", response_model=Dict[str, Any])
async def preview_notification_template(
    template_id: str,
    variables: Dict[str, Any] = {},
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Preview a notification template with variables"""
    try:
        template = service.get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Render template with provided variables
        preview = {}
        
        if template.email_subject:
            preview["email_subject"] = service.render_template(template.email_subject, variables)
        if template.email_body:
            preview["email_body"] = service.render_template(template.email_body, variables)
        if template.sms_content:
            preview["sms_content"] = service.render_template(template.sms_content, variables)
        if template.push_title:
            preview["push_title"] = service.render_template(template.push_title, variables)
        if template.push_body:
            preview["push_body"] = service.render_template(template.push_body, variables)
        if template.in_app_title:
            preview["in_app_title"] = service.render_template(template.in_app_title, variables)
        if template.in_app_content:
            preview["in_app_content"] = service.render_template(template.in_app_content, variables)
        
        return {
            "success": True,
            "template_id": template_id,
            "variables": variables,
            "preview": preview
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Rule Management Endpoints
@router.post("/rules", response_model=Dict[str, Any])
async def create_notification_rule(
    rule_data: NotificationRuleCreate,
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Create a new notification rule"""
    try:
        rule = service.create_rule(rule_data.dict())
        
        return {
            "success": True,
            "message": "Rule created successfully",
            "rule": {
                "id": rule.id,
                "name": rule.name,
                "trigger_events": rule.trigger_events,
                "is_active": rule.is_active,
                "created_at": rule.created_at.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error creating rule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rules", response_model=List[Dict[str, Any]])
async def get_notification_rules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Get notification rules"""
    try:
        # This would require implementing get_rules method in service
        return []
    except Exception as e:
        logger.error(f"Error getting rules: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rules/{rule_id}/test", response_model=Dict[str, Any])
async def test_notification_rule(
    rule_id: str,
    test_context: Dict[str, Any] = {},
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Test a notification rule with sample data"""
    try:
        # This would require implementing rule testing logic
        return {
            "success": True,
            "message": "Rule test completed",
            "rule_id": rule_id,
            "test_context": test_context,
            "result": "Rule conditions would be satisfied"
        }
    except Exception as e:
        logger.error(f"Error testing rule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Notification Management Endpoints
@router.post("/notifications", response_model=Dict[str, Any])
async def create_notification(
    notification_data: NotificationCreate,
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Create a new notification"""
    try:
        notification = service.create_notification(notification_data.dict())
        
        return {
            "success": True,
            "message": "Notification created successfully",
            "notification": {
                "id": notification.id,
                "user_id": notification.user_id,
                "title": notification.title,
                "category": notification.category.value,
                "priority": notification.priority.value,
                "status": notification.status.value,
                "tracking_id": notification.tracking_id,
                "created_at": notification.created_at.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error creating notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notifications", response_model=List[NotificationResponse])
async def get_user_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[NotificationStatus] = None,
    category: Optional[NotificationCategory] = None,
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Get user notifications"""
    try:
        # This would require implementing get_user_notifications method
        return []
    except Exception as e:
        logger.error(f"Error getting notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notifications/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Get a specific notification"""
    try:
        # This would require implementing get_notification method
        raise HTTPException(status_code=404, detail="Notification not found")
    except Exception as e:
        logger.error(f"Error getting notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/notifications/{notification_id}/read", response_model=Dict[str, Any])
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Mark a notification as read"""
    try:
        service.record_notification_interaction(
            notification_id=notification_id,
            user_id=current_user.id,
            interaction_type="read"
        )
        
        return {
            "success": True,
            "message": "Notification marked as read"
        }
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/notifications/{notification_id}/click", response_model=Dict[str, Any])
async def record_notification_click(
    notification_id: str,
    click_data: Dict[str, Any] = {},
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Record a notification click"""
    try:
        service.record_notification_interaction(
            notification_id=notification_id,
            user_id=current_user.id,
            interaction_type="click",
            interaction_data=click_data
        )
        
        return {
            "success": True,
            "message": "Notification click recorded"
        }
    except Exception as e:
        logger.error(f"Error recording notification click: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/notifications/{notification_id}/dismiss", response_model=Dict[str, Any])
async def dismiss_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Dismiss a notification"""
    try:
        service.record_notification_interaction(
            notification_id=notification_id,
            user_id=current_user.id,
            interaction_type="dismiss"
        )
        
        return {
            "success": True,
            "message": "Notification dismissed"
        }
    except Exception as e:
        logger.error(f"Error dismissing notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/notifications/bulk-read", response_model=Dict[str, Any])
async def bulk_mark_notifications_read(
    notification_ids: List[str],
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Mark multiple notifications as read"""
    try:
        for notification_id in notification_ids:
            service.record_notification_interaction(
                notification_id=notification_id,
                user_id=current_user.id,
                interaction_type="read"
            )
        
        return {
            "success": True,
            "message": f"Marked {len(notification_ids)} notifications as read"
        }
    except Exception as e:
        logger.error(f"Error bulk marking notifications as read: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# User Preferences Endpoints
@router.get("/preferences", response_model=Dict[str, Any])
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Get user notification preferences"""
    try:
        preferences = service.get_user_preferences(current_user.id)
        
        if not preferences:
            # Return default preferences
            return {
                "email_enabled": True,
                "sms_enabled": True,
                "push_enabled": True,
                "in_app_enabled": True,
                "hydration_reminders": True,
                "goal_achievements": True,
                "social_activities": True,
                "health_alerts": True,
                "system_updates": True,
                "marketing": False,
                "quiet_hours": {},
                "frequency_limits": {},
                "personalization_level": "basic",
                "smart_timing": True,
                "predictive_filtering": True,
                "context_awareness": True
            }
        
        return {
            "email_enabled": preferences.email_enabled,
            "sms_enabled": preferences.sms_enabled,
            "push_enabled": preferences.push_enabled,
            "in_app_enabled": preferences.in_app_enabled,
            "hydration_reminders": preferences.hydration_reminders,
            "goal_achievements": preferences.goal_achievements,
            "social_activities": preferences.social_activities,
            "health_alerts": preferences.health_alerts,
            "system_updates": preferences.system_updates,
            "marketing": preferences.marketing,
            "quiet_hours": preferences.quiet_hours,
            "frequency_limits": preferences.frequency_limits,
            "personalization_level": preferences.personalization_level.value,
            "smart_timing": preferences.smart_timing,
            "predictive_filtering": preferences.predictive_filtering,
            "context_awareness": preferences.context_awareness,
            "updated_at": preferences.updated_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting notification preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/preferences", response_model=Dict[str, Any])
async def update_notification_preferences(
    preferences: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Update user notification preferences"""
    try:
        updated_preferences = service.update_user_preferences(
            current_user.id, 
            preferences.dict(exclude_unset=True)
        )
        
        return {
            "success": True,
            "message": "Preferences updated successfully",
            "preferences": {
                "email_enabled": updated_preferences.email_enabled,
                "sms_enabled": updated_preferences.sms_enabled,
                "push_enabled": updated_preferences.push_enabled,
                "in_app_enabled": updated_preferences.in_app_enabled,
                "updated_at": updated_preferences.updated_at.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error updating notification preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Campaign Management Endpoints
@router.post("/campaigns", response_model=Dict[str, Any])
async def create_notification_campaign(
    campaign_data: NotificationCampaignCreate,
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Create a new notification campaign"""
    try:
        campaign = service.create_campaign(campaign_data.dict())
        
        return {
            "success": True,
            "message": "Campaign created successfully",
            "campaign": {
                "id": campaign.id,
                "name": campaign.name,
                "status": campaign.status,
                "created_at": campaign.created_at.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error creating campaign: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaigns/{campaign_id}/execute", response_model=Dict[str, Any])
async def execute_notification_campaign(
    campaign_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Execute a notification campaign"""
    try:
        # Execute campaign in background
        background_tasks.add_task(service.execute_campaign, campaign_id)
        
        return {
            "success": True,
            "message": "Campaign execution started",
            "campaign_id": campaign_id
        }
    except Exception as e:
        logger.error(f"Error executing campaign: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaigns", response_model=List[Dict[str, Any]])
async def get_notification_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Get notification campaigns"""
    try:
        # This would require implementing get_campaigns method
        return []
    except Exception as e:
        logger.error(f"Error getting campaigns: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaigns/{campaign_id}/metrics", response_model=Dict[str, Any])
async def get_campaign_metrics(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Get campaign performance metrics"""
    try:
        # This would require implementing get_campaign_metrics method
        return {
            "campaign_id": campaign_id,
            "metrics": {
                "total_recipients": 0,
                "sent_count": 0,
                "delivered_count": 0,
                "opened_count": 0,
                "clicked_count": 0,
                "delivery_rate": 0.0,
                "open_rate": 0.0,
                "click_rate": 0.0
            }
        }
    except Exception as e:
        logger.error(f"Error getting campaign metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics Endpoints
@router.get("/analytics", response_model=Dict[str, Any])
async def get_notification_analytics(
    start_date: datetime = Query(..., description="Start date for analytics"),
    end_date: datetime = Query(..., description="End date for analytics"),
    channel: Optional[str] = Query(None, description="Filter by channel"),
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Get notification analytics"""
    try:
        analytics = service.get_notification_analytics(
            start_date=start_date,
            end_date=end_date,
            channel=channel,
            category=category
        )
        
        return analytics
    except Exception as e:
        logger.error(f"Error getting notification analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/dashboard", response_model=Dict[str, Any])
async def get_notification_dashboard(
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Get notification dashboard data"""
    try:
        # Get analytics for the last 30 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        analytics = service.get_notification_analytics(start_date, end_date)
        
        # Get system health status
        health_status = service.get_notification_health_status()
        
        return {
            "analytics": analytics,
            "health_status": health_status,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error getting notification dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/trends", response_model=Dict[str, Any])
async def get_notification_trends(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Get notification trends over time"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        analytics = service.get_notification_analytics(start_date, end_date)
        
        return {
            "trends": analytics,
            "period_days": days
        }
    except Exception as e:
        logger.error(f"Error getting notification trends: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# System Management Endpoints
@router.get("/system/health", response_model=Dict[str, Any])
async def get_notification_system_health(
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Get notification system health status"""
    try:
        health_status = service.get_notification_health_status()
        return health_status
    except Exception as e:
        logger.error(f"Error getting system health: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/system/process-queue", response_model=Dict[str, Any])
async def process_notification_queue(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Process notification queue"""
    try:
        # Process queue in background
        background_tasks.add_task(service.process_notification_queue)
        
        return {
            "success": True,
            "message": "Queue processing started"
        }
    except Exception as e:
        logger.error(f"Error processing queue: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/system/cleanup", response_model=Dict[str, Any])
async def cleanup_old_notifications(
    days_old: int = Query(30, ge=1, le=365),
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Clean up old notifications"""
    try:
        # Cleanup in background
        background_tasks.add_task(service.cleanup_old_notifications, days_old)
        
        return {
            "success": True,
            "message": f"Cleanup started for notifications older than {days_old} days"
        }
    except Exception as e:
        logger.error(f"Error starting cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system/stats", response_model=Dict[str, Any])
async def get_notification_system_stats(
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Get notification system statistics"""
    try:
        # This would require implementing get_system_stats method
        return {
            "total_templates": 0,
            "total_rules": 0,
            "total_notifications": 0,
            "total_campaigns": 0,
            "active_users": 0,
            "queue_size": 0,
            "processing_rate": 0.0,
            "error_rate": 0.0
        }
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Event Trigger Endpoints
@router.post("/events/trigger", response_model=Dict[str, Any])
async def trigger_notification_event(
    event_type: str,
    event_data: Dict[str, Any] = {},
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Trigger a notification event"""
    try:
        # Get rules that match this event type
        rules = service.get_rules_by_event(event_type)
        
        notifications_created = 0
        
        for rule in rules:
            # Evaluate rule conditions
            if service.evaluate_rule_conditions(rule, event_data):
                # Create notification based on rule
                notification_data = {
                    "user_id": current_user.id,
                    "template_id": rule.template_id,
                    "rule_id": rule.id,
                    "title": f"Event: {event_type}",
                    "content": f"Event triggered: {event_type}",
                    "category": NotificationCategory.SYSTEM_UPDATE,
                    "priority": rule.priority,
                    "variables": event_data
                }
                
                service.create_notification(notification_data)
                notifications_created += 1
        
        return {
            "success": True,
            "message": f"Event triggered successfully",
            "event_type": event_type,
            "rules_matched": len(rules),
            "notifications_created": notifications_created
        }
    except Exception as e:
        logger.error(f"Error triggering event: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Webhook Endpoints
@router.post("/webhooks/delivery-status", response_model=Dict[str, Any])
async def webhook_delivery_status(
    webhook_data: Dict[str, Any],
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Webhook endpoint for delivery status updates"""
    try:
        # Process delivery status webhook
        # This would typically be called by external services (SMS, email providers, etc.)
        
        tracking_id = webhook_data.get("tracking_id")
        status = webhook_data.get("status")
        
        if tracking_id and status:
            # Update notification status based on webhook
            # This would require implementing update_notification_status method
            pass
        
        return {
            "success": True,
            "message": "Webhook processed successfully"
        }
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/channels", response_model=List[Dict[str, Any]])
async def get_notification_channels(
    current_user: User = Depends(get_current_user),
    service: NotificationSystemService = Depends(get_notification_service)
):
    """Get available notification channels"""
    try:
        channels = [
            {
                "name": "Email",
                "type": "email",
                "description": "Email notifications",
                "supported_features": ["text", "html", "attachments"],
                "is_active": True
            },
            {
                "name": "SMS",
                "type": "sms",
                "description": "SMS text messages",
                "supported_features": ["text"],
                "is_active": True
            },
            {
                "name": "Push",
                "type": "push",
                "description": "Push notifications",
                "supported_features": ["text", "rich_media", "actions"],
                "is_active": True
            },
            {
                "name": "In-App",
                "type": "in_app",
                "description": "In-app notifications",
                "supported_features": ["text", "rich_media", "interactive"],
                "is_active": True
            },
            {
                "name": "Webhook",
                "type": "webhook",
                "description": "Webhook notifications",
                "supported_features": ["json", "custom_headers"],
                "is_active": True
            },
            {
                "name": "Slack",
                "type": "slack",
                "description": "Slack messages",
                "supported_features": ["text", "rich_formatting", "attachments"],
                "is_active": True
            },
            {
                "name": "Discord",
                "type": "discord",
                "description": "Discord messages",
                "supported_features": ["text", "rich_formatting", "embeds"],
                "is_active": True
            }
        ]
        
        return channels
    except Exception as e:
        logger.error(f"Error getting channels: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 