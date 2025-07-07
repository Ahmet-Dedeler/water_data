from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
import json
import uuid
import asyncio
import logging
from enum import Enum
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from jinja2 import Template
import schedule
import time
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import websockets
from dataclasses import dataclass
from pydantic import BaseModel

from app.models.notification_system import (
    NotificationTemplate, NotificationChannel, NotificationRule, 
    Notification, NotificationDeliveryLog, NotificationInteraction,
    NotificationCampaign, NotificationPreference, NotificationQueue,
    NotificationAnalytics, NotificationChannel as ChannelEnum,
    NotificationPriority, NotificationStatus, NotificationCategory,
    DeliveryMethod, PersonalizationLevel, TemplateType
)
from app.models.user import User
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class DeliveryResult:
    success: bool
    message: str
    external_id: Optional[str] = None
    delivery_time: Optional[datetime] = None
    response_data: Optional[Dict] = None

class NotificationSystemService:
    def __init__(self, db: Session):
        self.db = db
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.delivery_providers = self._initialize_providers()
        self.template_cache = {}
        self.rule_cache = {}
        
    def _initialize_providers(self) -> Dict[str, Any]:
        """Initialize delivery providers for different channels"""
        return {
            "email": {
                "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
                "smtp_port": int(os.getenv("SMTP_PORT", "587")),
                "smtp_username": os.getenv("SMTP_USERNAME"),
                "smtp_password": os.getenv("SMTP_PASSWORD"),
                "from_email": os.getenv("FROM_EMAIL"),
            },
            "sms": {
                "twilio_sid": os.getenv("TWILIO_SID"),
                "twilio_token": os.getenv("TWILIO_TOKEN"),
                "twilio_phone": os.getenv("TWILIO_PHONE"),
            },
            "push": {
                "fcm_server_key": os.getenv("FCM_SERVER_KEY"),
                "apns_key": os.getenv("APNS_KEY"),
                "apns_key_id": os.getenv("APNS_KEY_ID"),
                "apns_team_id": os.getenv("APNS_TEAM_ID"),
            },
            "webhook": {
                "default_timeout": 30,
                "retry_attempts": 3,
                "retry_delay": 5,
            },
            "slack": {
                "bot_token": os.getenv("SLACK_BOT_TOKEN"),
                "webhook_url": os.getenv("SLACK_WEBHOOK_URL"),
            },
            "discord": {
                "bot_token": os.getenv("DISCORD_BOT_TOKEN"),
                "webhook_url": os.getenv("DISCORD_WEBHOOK_URL"),
            }
        }

    # Template Management
    def create_template(self, template_data: Dict[str, Any]) -> NotificationTemplate:
        """Create a new notification template"""
        try:
            template = NotificationTemplate(
                id=str(uuid.uuid4()),
                name=template_data["name"],
                description=template_data.get("description"),
                category=template_data["category"],
                template_type=template_data.get("template_type", TemplateType.BASIC),
                email_subject=template_data.get("email_subject"),
                email_body=template_data.get("email_body"),
                email_html=template_data.get("email_html"),
                sms_content=template_data.get("sms_content"),
                push_title=template_data.get("push_title"),
                push_body=template_data.get("push_body"),
                in_app_title=template_data.get("in_app_title"),
                in_app_content=template_data.get("in_app_content"),
                variables=template_data.get("variables", {}),
                personalization_rules=template_data.get("personalization_rules", {}),
                localization=template_data.get("localization", {}),
                media_assets=template_data.get("media_assets", {}),
                interactive_elements=template_data.get("interactive_elements", {}),
                author_id=template_data.get("author_id"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(template)
            self.db.commit()
            self.db.refresh(template)
            
            # Clear template cache
            self.template_cache.clear()
            
            logger.info(f"Created notification template: {template.name}")
            return template
            
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            self.db.rollback()
            raise

    def get_templates(self, skip: int = 0, limit: int = 100, 
                     category: Optional[NotificationCategory] = None,
                     template_type: Optional[TemplateType] = None,
                     is_active: Optional[bool] = None) -> List[NotificationTemplate]:
        """Get notification templates with filtering"""
        query = self.db.query(NotificationTemplate)
        
        if category:
            query = query.filter(NotificationTemplate.category == category)
        if template_type:
            query = query.filter(NotificationTemplate.template_type == template_type)
        if is_active is not None:
            query = query.filter(NotificationTemplate.is_active == is_active)
            
        return query.order_by(desc(NotificationTemplate.created_at)).offset(skip).limit(limit).all()

    def get_template_by_id(self, template_id: str) -> Optional[NotificationTemplate]:
        """Get template by ID with caching"""
        if template_id in self.template_cache:
            return self.template_cache[template_id]
            
        template = self.db.query(NotificationTemplate).filter(
            NotificationTemplate.id == template_id
        ).first()
        
        if template:
            self.template_cache[template_id] = template
            
        return template

    def update_template(self, template_id: str, update_data: Dict[str, Any]) -> Optional[NotificationTemplate]:
        """Update notification template"""
        try:
            template = self.get_template_by_id(template_id)
            if not template:
                return None
                
            for key, value in update_data.items():
                if hasattr(template, key) and value is not None:
                    setattr(template, key, value)
                    
            template.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(template)
            
            # Clear cache
            self.template_cache.pop(template_id, None)
            
            logger.info(f"Updated notification template: {template_id}")
            return template
            
        except Exception as e:
            logger.error(f"Error updating template: {str(e)}")
            self.db.rollback()
            raise

    def delete_template(self, template_id: str) -> bool:
        """Delete notification template"""
        try:
            template = self.get_template_by_id(template_id)
            if not template:
                return False
                
            # Check if template is in use
            notification_count = self.db.query(Notification).filter(
                Notification.template_id == template_id
            ).count()
            
            if notification_count > 0:
                # Soft delete - mark as inactive
                template.is_active = False
                template.updated_at = datetime.utcnow()
            else:
                # Hard delete
                self.db.delete(template)
                
            self.db.commit()
            
            # Clear cache
            self.template_cache.pop(template_id, None)
            
            logger.info(f"Deleted notification template: {template_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting template: {str(e)}")
            self.db.rollback()
            raise

    def clone_template(self, template_id: str, new_name: str) -> Optional[NotificationTemplate]:
        """Clone an existing template"""
        try:
            original = self.get_template_by_id(template_id)
            if not original:
                return None
                
            cloned = NotificationTemplate(
                id=str(uuid.uuid4()),
                name=new_name,
                description=f"Cloned from {original.name}",
                category=original.category,
                template_type=original.template_type,
                email_subject=original.email_subject,
                email_body=original.email_body,
                email_html=original.email_html,
                sms_content=original.sms_content,
                push_title=original.push_title,
                push_body=original.push_body,
                in_app_title=original.in_app_title,
                in_app_content=original.in_app_content,
                variables=original.variables,
                personalization_rules=original.personalization_rules,
                localization=original.localization,
                media_assets=original.media_assets,
                interactive_elements=original.interactive_elements,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(cloned)
            self.db.commit()
            self.db.refresh(cloned)
            
            logger.info(f"Cloned template {template_id} to {cloned.id}")
            return cloned
            
        except Exception as e:
            logger.error(f"Error cloning template: {str(e)}")
            self.db.rollback()
            raise

    # Rule Management
    def create_rule(self, rule_data: Dict[str, Any]) -> NotificationRule:
        """Create a new notification rule"""
        try:
            rule = NotificationRule(
                id=str(uuid.uuid4()),
                name=rule_data["name"],
                description=rule_data.get("description"),
                trigger_events=rule_data["trigger_events"],
                conditions=rule_data.get("conditions", {}),
                filters=rule_data.get("filters", {}),
                template_id=rule_data["template_id"],
                channels=rule_data["channels"],
                priority=rule_data.get("priority", NotificationPriority.NORMAL),
                schedule_type=rule_data.get("schedule_type", DeliveryMethod.IMMEDIATE),
                schedule_config=rule_data.get("schedule_config", {}),
                timezone_aware=rule_data.get("timezone_aware", True),
                max_frequency=rule_data.get("max_frequency", {}),
                personalization_level=rule_data.get("personalization_level", PersonalizationLevel.BASIC),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(rule)
            self.db.commit()
            self.db.refresh(rule)
            
            # Clear rule cache
            self.rule_cache.clear()
            
            logger.info(f"Created notification rule: {rule.name}")
            return rule
            
        except Exception as e:
            logger.error(f"Error creating rule: {str(e)}")
            self.db.rollback()
            raise

    def get_rules_by_event(self, event_type: str) -> List[NotificationRule]:
        """Get rules that match a specific event type"""
        cache_key = f"rules_{event_type}"
        if cache_key in self.rule_cache:
            return self.rule_cache[cache_key]
            
        rules = self.db.query(NotificationRule).filter(
            and_(
                NotificationRule.is_active == True,
                NotificationRule.trigger_events.contains([event_type])
            )
        ).all()
        
        self.rule_cache[cache_key] = rules
        return rules

    def evaluate_rule_conditions(self, rule: NotificationRule, context: Dict[str, Any]) -> bool:
        """Evaluate if rule conditions are met"""
        try:
            if not rule.conditions:
                return True
                
            # Simple condition evaluation (can be enhanced with a rule engine)
            for condition_key, condition_value in rule.conditions.items():
                context_value = context.get(condition_key)
                
                if isinstance(condition_value, dict):
                    # Handle complex conditions
                    if "operator" in condition_value:
                        operator = condition_value["operator"]
                        expected_value = condition_value["value"]
                        
                        if operator == "eq" and context_value != expected_value:
                            return False
                        elif operator == "ne" and context_value == expected_value:
                            return False
                        elif operator == "gt" and context_value <= expected_value:
                            return False
                        elif operator == "lt" and context_value >= expected_value:
                            return False
                        elif operator == "gte" and context_value < expected_value:
                            return False
                        elif operator == "lte" and context_value > expected_value:
                            return False
                        elif operator == "in" and context_value not in expected_value:
                            return False
                        elif operator == "not_in" and context_value in expected_value:
                            return False
                else:
                    # Simple equality check
                    if context_value != condition_value:
                        return False
                        
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating rule conditions: {str(e)}")
            return False

    # Notification Creation and Management
    def create_notification(self, notification_data: Dict[str, Any]) -> Notification:
        """Create a new notification"""
        try:
            notification = Notification(
                id=str(uuid.uuid4()),
                user_id=notification_data["user_id"],
                template_id=notification_data.get("template_id"),
                rule_id=notification_data.get("rule_id"),
                title=notification_data["title"],
                content=notification_data["content"],
                rich_content=notification_data.get("rich_content", {}),
                category=notification_data["category"],
                priority=notification_data.get("priority", NotificationPriority.NORMAL),
                scheduled_at=notification_data.get("scheduled_at"),
                expires_at=notification_data.get("expires_at"),
                variables=notification_data.get("variables", {}),
                personalization_data=notification_data.get("personalization_data", {}),
                tracking_id=str(uuid.uuid4()),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(notification)
            self.db.commit()
            self.db.refresh(notification)
            
            # Queue for delivery if not scheduled
            if not notification.scheduled_at or notification.scheduled_at <= datetime.utcnow():
                self.queue_notification(notification)
            
            logger.info(f"Created notification: {notification.id}")
            return notification
            
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            self.db.rollback()
            raise

    def queue_notification(self, notification: Notification) -> None:
        """Queue notification for delivery"""
        try:
            # Calculate priority score
            priority_scores = {
                NotificationPriority.LOW: 1,
                NotificationPriority.NORMAL: 5,
                NotificationPriority.HIGH: 10,
                NotificationPriority.URGENT: 15,
                NotificationPriority.CRITICAL: 20
            }
            
            queue_item = NotificationQueue(
                id=str(uuid.uuid4()),
                notification_id=notification.id,
                queue_name=f"notifications_{notification.priority.value}",
                priority_score=priority_scores.get(notification.priority, 5),
                scheduled_for=notification.scheduled_at or datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(queue_item)
            self.db.commit()
            
            logger.info(f"Queued notification: {notification.id}")
            
        except Exception as e:
            logger.error(f"Error queuing notification: {str(e)}")
            self.db.rollback()
            raise

    def process_notification_queue(self) -> int:
        """Process notifications in the queue"""
        try:
            # Get notifications ready for delivery
            ready_notifications = self.db.query(NotificationQueue).join(
                Notification
            ).filter(
                and_(
                    NotificationQueue.status == "queued",
                    NotificationQueue.scheduled_for <= datetime.utcnow(),
                    NotificationQueue.attempts < NotificationQueue.max_attempts
                )
            ).order_by(
                desc(NotificationQueue.priority_score),
                asc(NotificationQueue.scheduled_for)
            ).limit(100).all()
            
            processed_count = 0
            
            for queue_item in ready_notifications:
                try:
                    # Mark as processing
                    queue_item.status = "processing"
                    queue_item.processing_started = datetime.utcnow()
                    queue_item.processor_id = f"worker_{os.getpid()}"
                    self.db.commit()
                    
                    # Get the notification
                    notification = self.db.query(Notification).filter(
                        Notification.id == queue_item.notification_id
                    ).first()
                    
                    if notification:
                        # Deliver the notification
                        success = self.deliver_notification(notification)
                        
                        if success:
                            queue_item.status = "completed"
                            queue_item.processing_completed = datetime.utcnow()
                        else:
                            queue_item.attempts += 1
                            if queue_item.attempts >= queue_item.max_attempts:
                                queue_item.status = "failed"
                            else:
                                queue_item.status = "queued"
                                queue_item.next_attempt = datetime.utcnow() + timedelta(minutes=5 * queue_item.attempts)
                        
                        self.db.commit()
                        processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing queue item {queue_item.id}: {str(e)}")
                    queue_item.status = "failed"
                    queue_item.error_details = {"error": str(e), "timestamp": datetime.utcnow().isoformat()}
                    self.db.commit()
            
            return processed_count
            
        except Exception as e:
            logger.error(f"Error processing notification queue: {str(e)}")
            return 0

    def deliver_notification(self, notification: Notification) -> bool:
        """Deliver a notification through appropriate channels"""
        try:
            # Get user preferences
            user_preferences = self.get_user_preferences(notification.user_id)
            
            # Determine delivery channels
            channels = self.determine_delivery_channels(notification, user_preferences)
            
            delivery_success = False
            
            for channel in channels:
                try:
                    result = self.deliver_to_channel(notification, channel)
                    
                    # Log delivery attempt
                    self.log_delivery_attempt(notification, channel, result)
                    
                    if result.success:
                        delivery_success = True
                        
                        # Update notification status
                        if not notification.sent_at:
                            notification.sent_at = datetime.utcnow()
                            notification.status = NotificationStatus.SENT
                            
                        if result.delivery_time:
                            notification.delivered_at = result.delivery_time
                            notification.status = NotificationStatus.DELIVERED
                            
                except Exception as e:
                    logger.error(f"Error delivering to channel {channel}: {str(e)}")
                    
            # Update notification
            notification.delivery_attempts += 1
            notification.last_attempt_at = datetime.utcnow()
            
            if not delivery_success:
                notification.status = NotificationStatus.FAILED
                
            self.db.commit()
            
            return delivery_success
            
        except Exception as e:
            logger.error(f"Error delivering notification {notification.id}: {str(e)}")
            return False

    def deliver_to_channel(self, notification: Notification, channel: ChannelEnum) -> DeliveryResult:
        """Deliver notification to a specific channel"""
        try:
            if channel == ChannelEnum.EMAIL:
                return self.deliver_email(notification)
            elif channel == ChannelEnum.SMS:
                return self.deliver_sms(notification)
            elif channel == ChannelEnum.PUSH:
                return self.deliver_push(notification)
            elif channel == ChannelEnum.IN_APP:
                return self.deliver_in_app(notification)
            elif channel == ChannelEnum.WEBHOOK:
                return self.deliver_webhook(notification)
            elif channel == ChannelEnum.SLACK:
                return self.deliver_slack(notification)
            elif channel == ChannelEnum.DISCORD:
                return self.deliver_discord(notification)
            else:
                return DeliveryResult(success=False, message=f"Unsupported channel: {channel}")
                
        except Exception as e:
            logger.error(f"Error delivering to channel {channel}: {str(e)}")
            return DeliveryResult(success=False, message=str(e))

    def deliver_email(self, notification: Notification) -> DeliveryResult:
        """Deliver notification via email"""
        try:
            # Get email configuration
            config = self.delivery_providers["email"]
            
            # Get user email
            user = self.db.query(User).filter(User.id == notification.user_id).first()
            if not user or not user.email:
                return DeliveryResult(success=False, message="User email not found")
            
            # Prepare email content
            template = self.get_template_by_id(notification.template_id) if notification.template_id else None
            
            if template and template.email_subject and template.email_body:
                subject = self.render_template(template.email_subject, notification.variables)
                body = self.render_template(template.email_body, notification.variables)
                html_body = self.render_template(template.email_html, notification.variables) if template.email_html else None
            else:
                subject = notification.title
                body = notification.content
                html_body = None
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = config["from_email"]
            msg['To'] = user.email
            
            # Add text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if available
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(config["smtp_server"], config["smtp_port"]) as server:
                server.starttls()
                server.login(config["smtp_username"], config["smtp_password"])
                server.send_message(msg)
            
            return DeliveryResult(
                success=True,
                message="Email sent successfully",
                delivery_time=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return DeliveryResult(success=False, message=str(e))

    def deliver_sms(self, notification: Notification) -> DeliveryResult:
        """Deliver notification via SMS"""
        try:
            # Get SMS configuration
            config = self.delivery_providers["sms"]
            
            # Get user phone number
            user = self.db.query(User).filter(User.id == notification.user_id).first()
            if not user or not hasattr(user, 'phone_number') or not user.phone_number:
                return DeliveryResult(success=False, message="User phone number not found")
            
            # Prepare SMS content
            template = self.get_template_by_id(notification.template_id) if notification.template_id else None
            
            if template and template.sms_content:
                content = self.render_template(template.sms_content, notification.variables)
            else:
                content = f"{notification.title}: {notification.content}"
            
            # Send SMS (mock implementation - replace with actual SMS provider)
            # This would typically use Twilio, AWS SNS, or similar service
            logger.info(f"Mock SMS sent to {user.phone_number}: {content}")
            
            return DeliveryResult(
                success=True,
                message="SMS sent successfully",
                delivery_time=datetime.utcnow(),
                external_id=f"sms_{uuid.uuid4()}"
            )
            
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            return DeliveryResult(success=False, message=str(e))

    def deliver_push(self, notification: Notification) -> DeliveryResult:
        """Deliver push notification"""
        try:
            # Get push configuration
            config = self.delivery_providers["push"]
            
            # Get user push tokens
            user = self.db.query(User).filter(User.id == notification.user_id).first()
            if not user:
                return DeliveryResult(success=False, message="User not found")
            
            # Prepare push content
            template = self.get_template_by_id(notification.template_id) if notification.template_id else None
            
            if template and template.push_title and template.push_body:
                title = self.render_template(template.push_title, notification.variables)
                body = self.render_template(template.push_body, notification.variables)
            else:
                title = notification.title
                body = notification.content
            
            # Send push notification (mock implementation)
            logger.info(f"Mock push notification sent to user {user.id}: {title} - {body}")
            
            return DeliveryResult(
                success=True,
                message="Push notification sent successfully",
                delivery_time=datetime.utcnow(),
                external_id=f"push_{uuid.uuid4()}"
            )
            
        except Exception as e:
            logger.error(f"Error sending push notification: {str(e)}")
            return DeliveryResult(success=False, message=str(e))

    def deliver_in_app(self, notification: Notification) -> DeliveryResult:
        """Deliver in-app notification"""
        try:
            # In-app notifications are stored in the database and retrieved by the client
            # Update notification status to indicate it's available in-app
            notification.status = NotificationStatus.DELIVERED
            notification.delivered_at = datetime.utcnow()
            
            return DeliveryResult(
                success=True,
                message="In-app notification delivered",
                delivery_time=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error delivering in-app notification: {str(e)}")
            return DeliveryResult(success=False, message=str(e))

    def deliver_webhook(self, notification: Notification) -> DeliveryResult:
        """Deliver notification via webhook"""
        try:
            # Get webhook configuration from user or system settings
            webhook_url = notification.variables.get("webhook_url")
            if not webhook_url:
                return DeliveryResult(success=False, message="Webhook URL not provided")
            
            # Prepare webhook payload
            payload = {
                "notification_id": notification.id,
                "user_id": notification.user_id,
                "title": notification.title,
                "content": notification.content,
                "category": notification.category.value,
                "priority": notification.priority.value,
                "timestamp": datetime.utcnow().isoformat(),
                "tracking_id": notification.tracking_id
            }
            
            # Send webhook (mock implementation)
            logger.info(f"Mock webhook sent to {webhook_url}: {json.dumps(payload)}")
            
            return DeliveryResult(
                success=True,
                message="Webhook sent successfully",
                delivery_time=datetime.utcnow(),
                external_id=f"webhook_{uuid.uuid4()}"
            )
            
        except Exception as e:
            logger.error(f"Error sending webhook: {str(e)}")
            return DeliveryResult(success=False, message=str(e))

    def deliver_slack(self, notification: Notification) -> DeliveryResult:
        """Deliver notification to Slack"""
        try:
            # Mock Slack delivery
            logger.info(f"Mock Slack message sent: {notification.title} - {notification.content}")
            
            return DeliveryResult(
                success=True,
                message="Slack message sent successfully",
                delivery_time=datetime.utcnow(),
                external_id=f"slack_{uuid.uuid4()}"
            )
            
        except Exception as e:
            logger.error(f"Error sending Slack message: {str(e)}")
            return DeliveryResult(success=False, message=str(e))

    def deliver_discord(self, notification: Notification) -> DeliveryResult:
        """Deliver notification to Discord"""
        try:
            # Mock Discord delivery
            logger.info(f"Mock Discord message sent: {notification.title} - {notification.content}")
            
            return DeliveryResult(
                success=True,
                message="Discord message sent successfully",
                delivery_time=datetime.utcnow(),
                external_id=f"discord_{uuid.uuid4()}"
            )
            
        except Exception as e:
            logger.error(f"Error sending Discord message: {str(e)}")
            return DeliveryResult(success=False, message=str(e))

    def render_template(self, template_content: str, variables: Dict[str, Any]) -> str:
        """Render template with variables"""
        try:
            template = Template(template_content)
            return template.render(**variables)
        except Exception as e:
            logger.error(f"Error rendering template: {str(e)}")
            return template_content

    def determine_delivery_channels(self, notification: Notification, 
                                  user_preferences: Optional[NotificationPreference]) -> List[ChannelEnum]:
        """Determine which channels to use for delivery"""
        channels = []
        
        if not user_preferences:
            # Default channels
            channels = [ChannelEnum.IN_APP, ChannelEnum.EMAIL]
        else:
            # Check user preferences
            if user_preferences.in_app_enabled:
                channels.append(ChannelEnum.IN_APP)
            if user_preferences.email_enabled:
                channels.append(ChannelEnum.EMAIL)
            if user_preferences.sms_enabled:
                channels.append(ChannelEnum.SMS)
            if user_preferences.push_enabled:
                channels.append(ChannelEnum.PUSH)
        
        # Priority-based channel selection
        if notification.priority in [NotificationPriority.URGENT, NotificationPriority.CRITICAL]:
            if ChannelEnum.SMS not in channels:
                channels.append(ChannelEnum.SMS)
            if ChannelEnum.PUSH not in channels:
                channels.append(ChannelEnum.PUSH)
        
        return channels

    def log_delivery_attempt(self, notification: Notification, channel: ChannelEnum, 
                           result: DeliveryResult) -> None:
        """Log delivery attempt"""
        try:
            log_entry = NotificationDeliveryLog(
                id=str(uuid.uuid4()),
                notification_id=notification.id,
                attempt_number=notification.delivery_attempts + 1,
                status=NotificationStatus.SENT if result.success else NotificationStatus.FAILED,
                delivery_time=result.delivery_time,
                external_id=result.external_id,
                provider_response=result.response_data,
                error_message=result.message if not result.success else None,
                created_at=datetime.utcnow()
            )
            
            self.db.add(log_entry)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error logging delivery attempt: {str(e)}")

    # User Preferences
    def get_user_preferences(self, user_id: str) -> Optional[NotificationPreference]:
        """Get user notification preferences"""
        return self.db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).first()

    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> NotificationPreference:
        """Update user notification preferences"""
        try:
            existing_prefs = self.get_user_preferences(user_id)
            
            if existing_prefs:
                # Update existing preferences
                for key, value in preferences.items():
                    if hasattr(existing_prefs, key) and value is not None:
                        setattr(existing_prefs, key, value)
                existing_prefs.updated_at = datetime.utcnow()
                self.db.commit()
                return existing_prefs
            else:
                # Create new preferences
                new_prefs = NotificationPreference(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    **preferences
                )
                self.db.add(new_prefs)
                self.db.commit()
                self.db.refresh(new_prefs)
                return new_prefs
                
        except Exception as e:
            logger.error(f"Error updating user preferences: {str(e)}")
            self.db.rollback()
            raise

    # Campaign Management
    def create_campaign(self, campaign_data: Dict[str, Any]) -> NotificationCampaign:
        """Create a notification campaign"""
        try:
            campaign = NotificationCampaign(
                id=str(uuid.uuid4()),
                name=campaign_data["name"],
                description=campaign_data.get("description"),
                template_id=campaign_data["template_id"],
                target_audience=campaign_data["target_audience"],
                channels=campaign_data["channels"],
                schedule=campaign_data["schedule"],
                start_date=campaign_data.get("start_date"),
                end_date=campaign_data.get("end_date"),
                ab_test_config=campaign_data.get("ab_test_config"),
                variants=campaign_data.get("variants"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(campaign)
            self.db.commit()
            self.db.refresh(campaign)
            
            logger.info(f"Created notification campaign: {campaign.name}")
            return campaign
            
        except Exception as e:
            logger.error(f"Error creating campaign: {str(e)}")
            self.db.rollback()
            raise

    def execute_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Execute a notification campaign"""
        try:
            campaign = self.db.query(NotificationCampaign).filter(
                NotificationCampaign.id == campaign_id
            ).first()
            
            if not campaign:
                return {"success": False, "message": "Campaign not found"}
            
            # Get target users based on audience criteria
            target_users = self.get_campaign_target_users(campaign)
            
            # Create notifications for each target user
            notifications_created = 0
            
            for user in target_users:
                try:
                    # Create notification for user
                    notification_data = {
                        "user_id": user.id,
                        "template_id": campaign.template_id,
                        "title": f"Campaign: {campaign.name}",
                        "content": f"You have a new message from {campaign.name}",
                        "category": NotificationCategory.MARKETING,
                        "priority": NotificationPriority.NORMAL,
                        "variables": {"campaign_name": campaign.name, "user_name": user.username}
                    }
                    
                    notification = self.create_notification(notification_data)
                    notifications_created += 1
                    
                except Exception as e:
                    logger.error(f"Error creating notification for user {user.id}: {str(e)}")
            
            # Update campaign metrics
            campaign.total_recipients = len(target_users)
            campaign.sent_count = notifications_created
            campaign.status = "active"
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Campaign executed successfully",
                "notifications_created": notifications_created,
                "target_users": len(target_users)
            }
            
        except Exception as e:
            logger.error(f"Error executing campaign: {str(e)}")
            return {"success": False, "message": str(e)}

    def get_campaign_target_users(self, campaign: NotificationCampaign) -> List[User]:
        """Get target users for a campaign based on audience criteria"""
        try:
            query = self.db.query(User)
            
            # Apply audience filters
            audience_criteria = campaign.target_audience
            
            if "age_range" in audience_criteria:
                age_range = audience_criteria["age_range"]
                if "min" in age_range:
                    query = query.filter(User.age >= age_range["min"])
                if "max" in age_range:
                    query = query.filter(User.age <= age_range["max"])
            
            if "location" in audience_criteria:
                location = audience_criteria["location"]
                if "country" in location:
                    query = query.filter(User.country == location["country"])
                if "city" in location:
                    query = query.filter(User.city == location["city"])
            
            if "activity_level" in audience_criteria:
                activity_level = audience_criteria["activity_level"]
                # This would require joining with user activity data
                # For now, we'll just return all users
                pass
            
            return query.limit(1000).all()  # Limit to prevent overwhelming the system
            
        except Exception as e:
            logger.error(f"Error getting campaign target users: {str(e)}")
            return []

    # Analytics
    def get_notification_analytics(self, start_date: datetime, end_date: datetime,
                                 channel: Optional[str] = None,
                                 category: Optional[str] = None) -> Dict[str, Any]:
        """Get notification analytics for a date range"""
        try:
            query = self.db.query(NotificationAnalytics).filter(
                and_(
                    NotificationAnalytics.date >= start_date,
                    NotificationAnalytics.date <= end_date
                )
            )
            
            if channel:
                query = query.filter(NotificationAnalytics.channel == channel)
            if category:
                query = query.filter(NotificationAnalytics.category == category)
            
            analytics = query.all()
            
            # Aggregate metrics
            total_sent = sum(a.sent_count for a in analytics)
            total_delivered = sum(a.delivered_count for a in analytics)
            total_opened = sum(a.opened_count for a in analytics)
            total_clicked = sum(a.clicked_count for a in analytics)
            total_failed = sum(a.failed_count for a in analytics)
            
            delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
            open_rate = (total_opened / total_delivered * 100) if total_delivered > 0 else 0
            click_rate = (total_clicked / total_opened * 100) if total_opened > 0 else 0
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "metrics": {
                    "total_sent": total_sent,
                    "total_delivered": total_delivered,
                    "total_opened": total_opened,
                    "total_clicked": total_clicked,
                    "total_failed": total_failed,
                    "delivery_rate": round(delivery_rate, 2),
                    "open_rate": round(open_rate, 2),
                    "click_rate": round(click_rate, 2)
                },
                "daily_breakdown": [
                    {
                        "date": a.date.isoformat(),
                        "sent": a.sent_count,
                        "delivered": a.delivered_count,
                        "opened": a.opened_count,
                        "clicked": a.clicked_count,
                        "failed": a.failed_count
                    }
                    for a in analytics
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting notification analytics: {str(e)}")
            return {"error": str(e)}

    def record_notification_interaction(self, notification_id: str, user_id: str,
                                      interaction_type: str, interaction_data: Dict[str, Any] = None) -> None:
        """Record a notification interaction"""
        try:
            interaction = NotificationInteraction(
                id=str(uuid.uuid4()),
                notification_id=notification_id,
                user_id=user_id,
                interaction_type=interaction_type,
                interaction_data=interaction_data or {},
                interaction_time=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            
            self.db.add(interaction)
            
            # Update notification status based on interaction
            notification = self.db.query(Notification).filter(
                Notification.id == notification_id
            ).first()
            
            if notification:
                if interaction_type == "read" and not notification.read_at:
                    notification.read_at = datetime.utcnow()
                    notification.status = NotificationStatus.READ
                elif interaction_type == "click":
                    # Track click interactions
                    pass
                elif interaction_type == "dismiss":
                    # Track dismissal
                    pass
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error recording notification interaction: {str(e)}")
            self.db.rollback()

    # Utility Methods
    def cleanup_old_notifications(self, days_old: int = 30) -> int:
        """Clean up old notifications"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Delete old notifications
            deleted_count = self.db.query(Notification).filter(
                and_(
                    Notification.created_at < cutoff_date,
                    Notification.status.in_([NotificationStatus.READ, NotificationStatus.EXPIRED])
                )
            ).delete()
            
            # Delete old delivery logs
            self.db.query(NotificationDeliveryLog).filter(
                NotificationDeliveryLog.created_at < cutoff_date
            ).delete()
            
            # Delete old queue items
            self.db.query(NotificationQueue).filter(
                and_(
                    NotificationQueue.created_at < cutoff_date,
                    NotificationQueue.status.in_(["completed", "failed"])
                )
            ).delete()
            
            self.db.commit()
            
            logger.info(f"Cleaned up {deleted_count} old notifications")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old notifications: {str(e)}")
            self.db.rollback()
            return 0

    def get_notification_health_status(self) -> Dict[str, Any]:
        """Get notification system health status"""
        try:
            # Queue status
            queue_counts = self.db.query(
                NotificationQueue.status,
                func.count(NotificationQueue.id).label('count')
            ).group_by(NotificationQueue.status).all()
            
            # Recent delivery rates
            recent_date = datetime.utcnow() - timedelta(hours=24)
            recent_notifications = self.db.query(Notification).filter(
                Notification.created_at >= recent_date
            ).all()
            
            total_recent = len(recent_notifications)
            delivered_recent = len([n for n in recent_notifications if n.status == NotificationStatus.DELIVERED])
            failed_recent = len([n for n in recent_notifications if n.status == NotificationStatus.FAILED])
            
            delivery_rate = (delivered_recent / total_recent * 100) if total_recent > 0 else 0
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "queue_status": {
                    status: count for status, count in queue_counts
                },
                "recent_24h": {
                    "total_notifications": total_recent,
                    "delivered": delivered_recent,
                    "failed": failed_recent,
                    "delivery_rate": round(delivery_rate, 2)
                },
                "system_health": "healthy" if delivery_rate > 90 else "degraded" if delivery_rate > 70 else "unhealthy"
            }
            
        except Exception as e:
            logger.error(f"Error getting notification health status: {str(e)}")
            return {"error": str(e)} 