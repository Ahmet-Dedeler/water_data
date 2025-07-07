import json
import csv
import io
import os
import zipfile
import hashlib
import logging
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any, Union, Tuple
from pathlib import Path
import asyncio
import aiofiles
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import pandas as pd
from jinja2 import Template
import base64
from cryptography.fernet import Fernet

from ..models.export_reports import (
    ExportRequest, ExportResponse, ReportRequest, ReportResponse,
    ExportData, UserDataExport, ReportData, GDPRRequest, DataPortabilityExport,
    PrivacySettings, ExportMetrics, ExportAuditLog, DataUsageStatistics,
    ScheduledExport, ScheduledReport, ExportQuota, BulkExportRequest,
    ExportValidation, ExportFormat, ReportType, ExportStatus, DataCategory,
    ReportSection, PrivacyLevel, ReportTemplate, TemplateComponent, TemplateVariable,
    ExportWorkflow, WorkflowExecution, WorkflowStep, NotificationTemplate,
    NotificationRule, NotificationDelivery, ThirdPartyIntegration, IntegrationSync,
    WebhookEndpoint, ExportAnalytics, UserExportProfile, ExportPerformanceMetrics,
    SecurityEvent, ComplianceReport, ExportConfiguration, SystemHealth
)

logger = logging.getLogger(__name__)


class ExportService:
    """Service for handling data exports and report generation."""
    
    def __init__(self):
        self.export_dir = Path("app/data/exports")
        self.report_dir = Path("app/data/reports")
        self.template_dir = Path("app/templates/reports")
        self.workflow_dir = Path("app/data/workflows")
        self.integration_dir = Path("app/data/integrations")
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.workflow_dir.mkdir(parents=True, exist_ok=True)
        self.integration_dir.mkdir(parents=True, exist_ok=True)
        
        # Encryption key for sensitive data
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        
        # File paths for data storage
        self.exports_file = Path("app/data/exports.json")
        self.reports_file = Path("app/data/reports.json")
        self.gdpr_requests_file = Path("app/data/gdpr_requests.json")
        self.audit_logs_file = Path("app/data/export_audit_logs.json")
        self.quotas_file = Path("app/data/export_quotas.json")
        self.scheduled_exports_file = Path("app/data/scheduled_exports.json")
        self.templates_file = Path("app/data/report_templates.json")
        self.workflows_file = Path("app/data/export_workflows.json")
        self.integrations_file = Path("app/data/integrations.json")
        self.notifications_file = Path("app/data/export_notifications.json")
        self.analytics_file = Path("app/data/export_analytics.json")
        self.security_events_file = Path("app/data/security_events.json")
        self.compliance_reports_file = Path("app/data/compliance_reports.json")
        
        # Performance metrics
        self.metrics = {
            "total_exports": 0,
            "successful_exports": 0,
            "failed_exports": 0,
            "average_processing_time": 0.0,
            "peak_concurrent_exports": 0,
            "current_queue_size": 0
        }
        
        # Initialize data files
        self._initialize_data_files()
    
    def _initialize_data_files(self):
        """Initialize data files if they don't exist."""
        files_to_init = [
            (self.exports_file, []),
            (self.reports_file, []),
            (self.gdpr_requests_file, []),
            (self.audit_logs_file, []),
            (self.quotas_file, []),
            (self.scheduled_exports_file, []),
            (self.templates_file, []),
            (self.workflows_file, []),
            (self.integrations_file, []),
            (self.notifications_file, []),
            (self.analytics_file, []),
            (self.security_events_file, []),
            (self.compliance_reports_file, [])
        ]
        
        for file_path, default_data in files_to_init:
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    json.dump(default_data, f, indent=2)
    
    # Template Management Methods
    
    async def create_report_template(self, template: ReportTemplate) -> ReportTemplate:
        """Create a new report template."""
        try:
            templates = await self._load_templates()
            templates.append(template.dict())
            await self._save_templates(templates)
            
            # Log template creation
            await self._log_audit_event(
                template.created_by, "template_created", None, 
                {"template_id": template.template_id, "template_name": template.name}
            )
            
            return template
            
        except Exception as e:
            logger.error(f"Error creating report template: {str(e)}")
            raise
    
    async def get_report_templates(self, user_id: int, category: Optional[str] = None,
                                 is_public: Optional[bool] = None) -> List[ReportTemplate]:
        """Get available report templates."""
        try:
            templates = await self._load_templates()
            result = []
            
            for template_data in templates:
                template = ReportTemplate(**template_data)
                
                # Filter by access permissions
                if not template.is_public and template.created_by != user_id:
                    continue
                
                # Filter by category
                if category and template.category != category:
                    continue
                
                # Filter by public status
                if is_public is not None and template.is_public != is_public:
                    continue
                
                result.append(template)
            
            # Sort by usage count and rating
            result.sort(key=lambda x: (x.usage_count, x.rating), reverse=True)
            return result
            
        except Exception as e:
            logger.error(f"Error getting report templates: {str(e)}")
            raise
    
    async def update_report_template(self, template_id: str, updates: Dict[str, Any],
                                   user_id: int) -> Optional[ReportTemplate]:
        """Update a report template."""
        try:
            templates = await self._load_templates()
            
            for i, template_data in enumerate(templates):
                if template_data.get('template_id') == template_id:
                    template = ReportTemplate(**template_data)
                    
                    # Check permissions
                    if template.created_by != user_id:
                        raise PermissionError("Not authorized to update this template")
                    
                    # Apply updates
                    for key, value in updates.items():
                        if hasattr(template, key):
                            setattr(template, key, value)
                    
                    template.updated_at = datetime.utcnow()
                    templates[i] = template.dict()
                    await self._save_templates(templates)
                    
                    # Log template update
                    await self._log_audit_event(
                        user_id, "template_updated", None,
                        {"template_id": template_id, "updates": list(updates.keys())}
                    )
                    
                    return template
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating report template: {str(e)}")
            raise
    
    async def delete_report_template(self, template_id: str, user_id: int) -> bool:
        """Delete a report template."""
        try:
            templates = await self._load_templates()
            
            for i, template_data in enumerate(templates):
                if template_data.get('template_id') == template_id:
                    template = ReportTemplate(**template_data)
                    
                    # Check permissions
                    if template.created_by != user_id:
                        raise PermissionError("Not authorized to delete this template")
                    
                    # Remove template
                    templates.pop(i)
                    await self._save_templates(templates)
                    
                    # Log template deletion
                    await self._log_audit_event(
                        user_id, "template_deleted", None,
                        {"template_id": template_id, "template_name": template.name}
                    )
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting report template: {str(e)}")
            raise
    
    async def clone_report_template(self, template_id: str, user_id: int,
                                  new_name: str) -> Optional[ReportTemplate]:
        """Clone an existing report template."""
        try:
            templates = await self._load_templates()
            
            for template_data in templates:
                if template_data.get('template_id') == template_id:
                    original_template = ReportTemplate(**template_data)
                    
                    # Check access permissions
                    if not original_template.is_public and original_template.created_by != user_id:
                        raise PermissionError("Not authorized to clone this template")
                    
                    # Create clone
                    cloned_template = ReportTemplate(
                        name=new_name,
                        description=f"Cloned from {original_template.name}",
                        report_type=original_template.report_type,
                        sections=original_template.sections.copy(),
                        default_format=original_template.default_format,
                        styling=original_template.styling.copy(),
                        layout_config=original_template.layout_config.copy(),
                        chart_config=original_template.chart_config.copy(),
                        category=original_template.category,
                        tags=original_template.tags.copy(),
                        created_by=user_id
                    )
                    
                    # Save cloned template
                    templates.append(cloned_template.dict())
                    await self._save_templates(templates)
                    
                    # Log template cloning
                    await self._log_audit_event(
                        user_id, "template_cloned", None,
                        {
                            "original_template_id": template_id,
                            "cloned_template_id": cloned_template.template_id,
                            "new_name": new_name
                        }
                    )
                    
                    return cloned_template
            
            return None
            
        except Exception as e:
            logger.error(f"Error cloning report template: {str(e)}")
            raise
    
    # Workflow Management Methods
    
    async def create_export_workflow(self, workflow: ExportWorkflow) -> ExportWorkflow:
        """Create a new export workflow."""
        try:
            workflows = await self._load_workflows()
            workflows.append(workflow.dict())
            await self._save_workflows(workflows)
            
            # Log workflow creation
            await self._log_audit_event(
                workflow.created_by, "workflow_created", None,
                {"workflow_id": workflow.workflow_id, "workflow_name": workflow.name}
            )
            
            return workflow
            
        except Exception as e:
            logger.error(f"Error creating export workflow: {str(e)}")
            raise
    
    async def execute_workflow(self, workflow_id: str, user_id: int,
                             trigger_data: Dict[str, Any] = {}) -> WorkflowExecution:
        """Execute an export workflow."""
        try:
            workflows = await self._load_workflows()
            workflow_data = None
            
            for wf_data in workflows:
                if wf_data.get('workflow_id') == workflow_id:
                    workflow_data = wf_data
                    break
            
            if not workflow_data:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            workflow = ExportWorkflow(**workflow_data)
            
            # Create workflow execution
            execution = WorkflowExecution(
                workflow_id=workflow_id,
                user_id=user_id,
                status=WorkflowStatus.PROCESSING,
                trigger_data=trigger_data,
                total_steps=len(workflow.steps)
            )
            
            # Execute workflow steps
            try:
                for i, step_config in enumerate(workflow.steps):
                    execution.current_step = i + 1
                    step_result = await self._execute_workflow_step(step_config, user_id, trigger_data)
                    execution.step_results.append(step_result)
                    
                    # Check for step failure
                    if not step_result.get('success', True):
                        execution.status = WorkflowStatus.FAILED
                        execution.error_message = step_result.get('error', 'Step execution failed')
                        break
                
                if execution.status != WorkflowStatus.FAILED:
                    execution.status = WorkflowStatus.COMPLETED
                
            except Exception as e:
                execution.status = WorkflowStatus.FAILED
                execution.error_message = str(e)
            
            execution.completed_at = datetime.utcnow()
            execution.duration_seconds = (
                execution.completed_at - execution.started_at
            ).total_seconds()
            
            # Update workflow execution count
            workflow.execution_count += 1
            workflow.last_execution = datetime.utcnow()
            await self._update_workflow(workflow)
            
            # Log workflow execution
            await self._log_audit_event(
                user_id, "workflow_executed", None,
                {
                    "workflow_id": workflow_id,
                    "execution_id": execution.execution_id,
                    "status": execution.status.value,
                    "duration_seconds": execution.duration_seconds
                }
            )
            
            return execution
            
        except Exception as e:
            logger.error(f"Error executing workflow: {str(e)}")
            raise
    
    async def _execute_workflow_step(self, step_config: Dict[str, Any], user_id: int,
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step."""
        try:
            step_type = step_config.get('type')
            step_config_data = step_config.get('config', {})
            
            if step_type == 'export':
                # Create export request
                export_request = ExportRequest(
                    user_id=user_id,
                    export_format=ExportFormat(step_config_data.get('format', 'json')),
                    data_categories=[DataCategory(cat) for cat in step_config_data.get('categories', [])],
                    **step_config_data
                )
                
                response = await self.create_export_request(export_request)
                return {
                    'success': True,
                    'export_id': response.export_id,
                    'step_type': step_type
                }
                
            elif step_type == 'report':
                # Create report request
                report_request = ReportRequest(
                    user_id=user_id,
                    report_type=ReportType(step_config_data.get('type', 'comprehensive')),
                    report_format=ExportFormat(step_config_data.get('format', 'pdf')),
                    **step_config_data
                )
                
                response = await self.create_report_request(report_request)
                return {
                    'success': True,
                    'report_id': response.report_id,
                    'step_type': step_type
                }
                
            elif step_type == 'notification':
                # Send notification
                await self._send_workflow_notification(step_config_data, user_id, context)
                return {
                    'success': True,
                    'step_type': step_type,
                    'notification_sent': True
                }
                
            elif step_type == 'integration':
                # Execute integration
                integration_result = await self._execute_integration_step(step_config_data, user_id, context)
                return {
                    'success': integration_result.get('success', False),
                    'step_type': step_type,
                    'integration_result': integration_result
                }
                
            else:
                return {
                    'success': False,
                    'error': f'Unknown step type: {step_type}',
                    'step_type': step_type
                }
                
        except Exception as e:
            logger.error(f"Error executing workflow step: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'step_type': step_config.get('type', 'unknown')
            }
    
    # Integration Management Methods
    
    async def create_integration(self, integration: ThirdPartyIntegration) -> ThirdPartyIntegration:
        """Create a new third-party integration."""
        try:
            integrations = await self._load_integrations()
            
            # Encrypt sensitive credentials
            if integration.credentials:
                encrypted_credentials = {}
                for key, value in integration.credentials.items():
                    if isinstance(value, str):
                        encrypted_credentials[key] = self.cipher.encrypt(value.encode()).decode()
                    else:
                        encrypted_credentials[key] = value
                integration.credentials = encrypted_credentials
            
            integrations.append(integration.dict())
            await self._save_integrations(integrations)
            
            # Log integration creation
            await self._log_audit_event(
                integration.user_id, "integration_created", None,
                {
                    "integration_id": integration.integration_id,
                    "service_type": integration.service_type.value,
                    "service_name": integration.service_name
                }
            )
            
            return integration
            
        except Exception as e:
            logger.error(f"Error creating integration: {str(e)}")
            raise
    
    async def sync_integration(self, integration_id: str, export_id: Optional[str] = None,
                             report_id: Optional[str] = None) -> IntegrationSync:
        """Synchronize data with a third-party integration."""
        try:
            integrations = await self._load_integrations()
            integration_data = None
            
            for int_data in integrations:
                if int_data.get('integration_id') == integration_id:
                    integration_data = int_data
                    break
            
            if not integration_data:
                raise ValueError(f"Integration {integration_id} not found")
            
            integration = ThirdPartyIntegration(**integration_data)
            
            # Create sync record
            sync = IntegrationSync(
                integration_id=integration_id,
                export_id=export_id,
                report_id=report_id,
                sync_type="upload",
                status="success"
            )
            
            # Perform actual sync based on service type
            if integration.service_type == IntegrationType.GOOGLE_DRIVE:
                sync_result = await self._sync_google_drive(integration, export_id, report_id)
            elif integration.service_type == IntegrationType.DROPBOX:
                sync_result = await self._sync_dropbox(integration, export_id, report_id)
            elif integration.service_type == IntegrationType.AWS_S3:
                sync_result = await self._sync_aws_s3(integration, export_id, report_id)
            else:
                sync_result = {"success": False, "error": "Unsupported integration type"}
            
            # Update sync record
            sync.status = "success" if sync_result.get("success") else "failed"
            sync.files_synced = sync_result.get("files_synced", 0)
            sync.bytes_synced = sync_result.get("bytes_synced", 0)
            sync.error_message = sync_result.get("error")
            sync.completed_at = datetime.utcnow()
            sync.duration_seconds = (sync.completed_at - sync.started_at).total_seconds()
            
            # Update integration statistics
            integration.sync_count += 1
            integration.last_sync = datetime.utcnow()
            if not sync_result.get("success"):
                integration.error_count += 1
                integration.last_error = sync_result.get("error")
            
            await self._update_integration(integration)
            
            # Log sync operation
            await self._log_audit_event(
                integration.user_id, "integration_synced", export_id or report_id,
                {
                    "integration_id": integration_id,
                    "sync_id": sync.sync_id,
                    "status": sync.status,
                    "files_synced": sync.files_synced
                }
            )
            
            return sync
            
        except Exception as e:
            logger.error(f"Error syncing integration: {str(e)}")
            raise
    
    # Analytics and Monitoring Methods
    
    async def generate_export_analytics(self, period_start: datetime,
                                      period_end: datetime) -> ExportAnalytics:
        """Generate comprehensive export analytics."""
        try:
            exports = await self._load_exports()
            
            # Filter exports by period
            period_exports = []
            for export_data in exports:
                export_response = export_data.get('response', {})
                created_at = datetime.fromisoformat(export_response.get('created_at', ''))
                if period_start <= created_at <= period_end:
                    period_exports.append(export_response)
            
            # Calculate metrics
            total_exports = len(period_exports)
            successful_exports = sum(1 for exp in period_exports if exp.get('status') == 'completed')
            failed_exports = sum(1 for exp in period_exports if exp.get('status') == 'failed')
            cancelled_exports = sum(1 for exp in period_exports if exp.get('status') == 'cancelled')
            
            # Calculate processing times
            processing_times = []
            for exp in period_exports:
                if exp.get('processing_time_seconds'):
                    processing_times.append(exp['processing_time_seconds'])
            
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            median_processing_time = sorted(processing_times)[len(processing_times) // 2] if processing_times else 0
            
            # Calculate data volume
            total_data_gb = sum(
                (exp.get('file_size_bytes', 0) or 0) / (1024 * 1024 * 1024)
                for exp in period_exports
            )
            
            # Analyze format popularity
            format_counts = {}
            for exp in period_exports:
                format_val = exp.get('export_format', 'unknown')
                format_counts[format_val] = format_counts.get(format_val, 0) + 1
            
            # Analyze category popularity
            category_counts = {}
            for export_data in exports:
                request = export_data.get('request', {})
                for category in request.get('data_categories', []):
                    category_counts[category] = category_counts.get(category, 0) + 1
            
            # Analyze peak hours
            hour_counts = {}
            for exp in period_exports:
                created_at = datetime.fromisoformat(exp.get('created_at', ''))
                hour = created_at.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            
            peak_hours = sorted(hour_counts.keys(), key=lambda h: hour_counts[h], reverse=True)[:5]
            
            # Get unique users
            unique_users = len(set(exp.get('user_id') for exp in period_exports if exp.get('user_id')))
            
            analytics = ExportAnalytics(
                period_start=period_start,
                period_end=period_end,
                total_exports=total_exports,
                successful_exports=successful_exports,
                failed_exports=failed_exports,
                cancelled_exports=cancelled_exports,
                average_processing_time=avg_processing_time,
                median_processing_time=median_processing_time,
                total_data_exported_gb=total_data_gb,
                unique_users=unique_users,
                popular_formats=format_counts,
                popular_categories=category_counts,
                peak_hours=peak_hours
            )
            
            # Save analytics
            analytics_data = await self._load_analytics()
            analytics_data.append(analytics.dict())
            await self._save_analytics(analytics_data)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating export analytics: {str(e)}")
            raise
    
    async def get_user_export_profile(self, user_id: int) -> UserExportProfile:
        """Get user's export behavior profile."""
        try:
            exports = await self.get_user_exports(user_id, 1, 1000)
            
            if not exports:
                return UserExportProfile(
                    user_id=user_id,
                    total_exports=0,
                    successful_exports=0,
                    failed_exports=0,
                    preferred_format=ExportFormat.JSON,
                    preferred_categories=[],
                    average_file_size_mb=0.0,
                    export_frequency_days=0.0,
                    most_active_hour=9,
                    most_active_day="monday"
                )
            
            # Calculate statistics
            total_exports = len(exports)
            successful_exports = sum(1 for exp in exports if exp.status == ExportStatus.COMPLETED)
            failed_exports = sum(1 for exp in exports if exp.status == ExportStatus.FAILED)
            
            # Find preferred format
            format_counts = {}
            for exp in exports:
                format_counts[exp.export_format] = format_counts.get(exp.export_format, 0) + 1
            
            preferred_format = max(format_counts, key=format_counts.get) if format_counts else ExportFormat.JSON
            
            # Calculate average file size
            file_sizes = [exp.file_size_bytes for exp in exports if exp.file_size_bytes]
            average_file_size_mb = (sum(file_sizes) / len(file_sizes)) / (1024 * 1024) if file_sizes else 0.0
            
            # Calculate export frequency
            if len(exports) > 1:
                first_export = min(exp.created_at for exp in exports)
                last_export = max(exp.created_at for exp in exports)
                days_span = (last_export - first_export).days
                export_frequency_days = days_span / len(exports) if days_span > 0 else 0.0
            else:
                export_frequency_days = 0.0
            
            # Find most active hour
            hour_counts = {}
            for exp in exports:
                hour = exp.created_at.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            
            most_active_hour = max(hour_counts, key=hour_counts.get) if hour_counts else 9
            
            # Find most active day
            day_counts = {}
            for exp in exports:
                day = exp.created_at.strftime('%A').lower()
                day_counts[day] = day_counts.get(day, 0) + 1
            
            most_active_day = max(day_counts, key=day_counts.get) if day_counts else "monday"
            
            # Get last export date
            last_export_date = max(exp.created_at for exp in exports).date() if exports else None
            
            profile = UserExportProfile(
                user_id=user_id,
                total_exports=total_exports,
                successful_exports=successful_exports,
                failed_exports=failed_exports,
                preferred_format=preferred_format,
                preferred_categories=[],  # Would need to analyze request data
                average_file_size_mb=average_file_size_mb,
                export_frequency_days=export_frequency_days,
                last_export_date=last_export_date,
                most_active_hour=most_active_hour,
                most_active_day=most_active_day
            )
            
            return profile
            
        except Exception as e:
            logger.error(f"Error getting user export profile: {str(e)}")
            raise
    
    # Security and Compliance Methods
    
    async def log_security_event(self, event: SecurityEvent) -> SecurityEvent:
        """Log a security event."""
        try:
            security_events = await self._load_security_events()
            security_events.append(event.dict())
            await self._save_security_events(security_events)
            
            # If critical event, trigger immediate alerts
            if event.severity == "critical":
                await self._trigger_security_alert(event)
            
            return event
            
        except Exception as e:
            logger.error(f"Error logging security event: {str(e)}")
            raise
    
    async def generate_compliance_report(self, report_type: str, period_start: datetime,
                                       period_end: datetime, generated_by: int) -> ComplianceReport:
        """Generate a compliance report."""
        try:
            # Get relevant data based on report type
            if report_type == "gdpr":
                gdpr_requests = await self._load_gdpr_requests()
                period_requests = [
                    req for req in gdpr_requests
                    if period_start <= datetime.fromisoformat(req.get('submitted_at', '')) <= period_end
                ]
                
                total_requests = len(period_requests)
                completed_requests = sum(1 for req in period_requests if req.get('status') == 'completed')
                pending_requests = sum(1 for req in period_requests if req.get('status') == 'pending')
                overdue_requests = sum(
                    1 for req in period_requests
                    if req.get('status') == 'pending' and 
                    datetime.fromisoformat(req.get('submitted_at', '')) < datetime.utcnow() - timedelta(days=30)
                )
                
                # Calculate average response time
                completed_request_times = []
                for req in period_requests:
                    if req.get('status') == 'completed' and req.get('processed_at'):
                        submitted = datetime.fromisoformat(req.get('submitted_at', ''))
                        processed = datetime.fromisoformat(req.get('processed_at', ''))
                        hours = (processed - submitted).total_seconds() / 3600
                        completed_request_times.append(hours)
                
                avg_response_time = sum(completed_request_times) / len(completed_request_times) if completed_request_times else 0
                
                # Calculate compliance score
                compliance_score = (completed_requests / total_requests * 100) if total_requests > 0 else 100
                
                # Identify violations
                violations = []
                if overdue_requests > 0:
                    violations.append({
                        "type": "overdue_requests",
                        "count": overdue_requests,
                        "description": f"{overdue_requests} GDPR requests are overdue (>30 days)"
                    })
                
                if avg_response_time > 720:  # 30 days in hours
                    violations.append({
                        "type": "slow_response",
                        "avg_hours": avg_response_time,
                        "description": f"Average response time ({avg_response_time:.1f} hours) exceeds 30 days"
                    })
                
                # Generate recommendations
                recommendations = []
                if overdue_requests > 0:
                    recommendations.append("Prioritize processing of overdue GDPR requests")
                if avg_response_time > 168:  # 7 days
                    recommendations.append("Implement automated processing for common request types")
                if compliance_score < 95:
                    recommendations.append("Review and optimize GDPR request handling procedures")
                
                report = ComplianceReport(
                    report_type=report_type,
                    period_start=period_start,
                    period_end=period_end,
                    total_requests=total_requests,
                    completed_requests=completed_requests,
                    pending_requests=pending_requests,
                    overdue_requests=overdue_requests,
                    average_response_time_hours=avg_response_time,
                    compliance_score=compliance_score,
                    violations=violations,
                    recommendations=recommendations,
                    generated_by=generated_by
                )
                
                # Save compliance report
                compliance_reports = await self._load_compliance_reports()
                compliance_reports.append(report.dict())
                await self._save_compliance_reports(compliance_reports)
                
                return report
            
            else:
                raise ValueError(f"Unsupported compliance report type: {report_type}")
                
        except Exception as e:
            logger.error(f"Error generating compliance report: {str(e)}")
            raise
    
    # Helper Methods for Data Persistence
    
    async def _load_templates(self) -> List[Dict]:
        """Load report templates from file."""
        if self.templates_file.exists():
            with open(self.templates_file, 'r') as f:
                return json.load(f)
        return []
    
    async def _save_templates(self, templates: List[Dict]):
        """Save report templates to file."""
        with open(self.templates_file, 'w') as f:
            json.dump(templates, f, indent=2, default=str)
    
    async def _load_workflows(self) -> List[Dict]:
        """Load workflows from file."""
        if self.workflows_file.exists():
            with open(self.workflows_file, 'r') as f:
                return json.load(f)
        return []
    
    async def _save_workflows(self, workflows: List[Dict]):
        """Save workflows to file."""
        with open(self.workflows_file, 'w') as f:
            json.dump(workflows, f, indent=2, default=str)
    
    async def _update_workflow(self, workflow: ExportWorkflow):
        """Update a workflow in storage."""
        workflows = await self._load_workflows()
        for i, wf_data in enumerate(workflows):
            if wf_data.get('workflow_id') == workflow.workflow_id:
                workflows[i] = workflow.dict()
                break
        await self._save_workflows(workflows)
    
    async def _load_integrations(self) -> List[Dict]:
        """Load integrations from file."""
        if self.integrations_file.exists():
            with open(self.integrations_file, 'r') as f:
                return json.load(f)
        return []
    
    async def _save_integrations(self, integrations: List[Dict]):
        """Save integrations to file."""
        with open(self.integrations_file, 'w') as f:
            json.dump(integrations, f, indent=2, default=str)
    
    async def _update_integration(self, integration: ThirdPartyIntegration):
        """Update an integration in storage."""
        integrations = await self._load_integrations()
        for i, int_data in enumerate(integrations):
            if int_data.get('integration_id') == integration.integration_id:
                integrations[i] = integration.dict()
                break
        await self._save_integrations(integrations)
    
    async def _load_analytics(self) -> List[Dict]:
        """Load analytics from file."""
        if self.analytics_file.exists():
            with open(self.analytics_file, 'r') as f:
                return json.load(f)
        return []
    
    async def _save_analytics(self, analytics: List[Dict]):
        """Save analytics to file."""
        with open(self.analytics_file, 'w') as f:
            json.dump(analytics, f, indent=2, default=str)
    
    async def _load_security_events(self) -> List[Dict]:
        """Load security events from file."""
        if self.security_events_file.exists():
            with open(self.security_events_file, 'r') as f:
                return json.load(f)
        return []
    
    async def _save_security_events(self, events: List[Dict]):
        """Save security events to file."""
        with open(self.security_events_file, 'w') as f:
            json.dump(events, f, indent=2, default=str)
    
    async def _load_compliance_reports(self) -> List[Dict]:
        """Load compliance reports from file."""
        if self.compliance_reports_file.exists():
            with open(self.compliance_reports_file, 'r') as f:
                return json.load(f)
        return []
    
    async def _save_compliance_reports(self, reports: List[Dict]):
        """Save compliance reports to file."""
        with open(self.compliance_reports_file, 'w') as f:
            json.dump(reports, f, indent=2, default=str)
    
    # Mock integration methods (would be implemented with actual APIs)
    
    async def _sync_google_drive(self, integration: ThirdPartyIntegration,
                               export_id: Optional[str], report_id: Optional[str]) -> Dict[str, Any]:
        """Mock Google Drive sync."""
        return {"success": True, "files_synced": 1, "bytes_synced": 1024000}
    
    async def _sync_dropbox(self, integration: ThirdPartyIntegration,
                          export_id: Optional[str], report_id: Optional[str]) -> Dict[str, Any]:
        """Mock Dropbox sync."""
        return {"success": True, "files_synced": 1, "bytes_synced": 1024000}
    
    async def _sync_aws_s3(self, integration: ThirdPartyIntegration,
                         export_id: Optional[str], report_id: Optional[str]) -> Dict[str, Any]:
        """Mock AWS S3 sync."""
        return {"success": True, "files_synced": 1, "bytes_synced": 1024000}
    
    async def _send_workflow_notification(self, config: Dict[str, Any], user_id: int,
                                        context: Dict[str, Any]):
        """Send workflow notification."""
        # Mock notification sending
        logger.info(f"Sending workflow notification to user {user_id}: {config.get('message', 'Workflow completed')}")
    
    async def _execute_integration_step(self, config: Dict[str, Any], user_id: int,
                                      context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute integration workflow step."""
        # Mock integration execution
        return {"success": True, "integration_type": config.get('type', 'unknown')}
    
    async def _trigger_security_alert(self, event: SecurityEvent):
        """Trigger security alert for critical events."""
        # Mock security alert
        logger.critical(f"SECURITY ALERT: {event.event_type} - {event.description}")

    # Export Management (existing methods continue here...)
    
    async def create_export_request(self, request: ExportRequest) -> ExportResponse:
        """Create a new export request."""
        try:
            # Check user quota
            if not await self._check_export_quota(request.user_id):
                raise ValueError("Export quota exceeded")
            
            # Create export response
            export_response = ExportResponse(
                export_id=request.export_id,
                user_id=request.user_id,
                status=ExportStatus.PENDING,
                export_format=request.export_format,
                created_at=request.created_at,
                expires_at=datetime.utcnow() + timedelta(days=request.retention_days),
                estimated_completion=datetime.utcnow() + timedelta(minutes=5)
            )
            
            # Save export request
            await self._save_export_request(request, export_response)
            
            # Log audit event
            await self._log_audit_event(request.user_id, "export_requested", request.export_id)
            
            # Start background processing
            asyncio.create_task(self._process_export_async(request, export_response))
            
            return export_response
            
        except Exception as e:
            logger.error(f"Error creating export request: {str(e)}")
            raise
    
    async def _process_export_async(self, request: ExportRequest, response: ExportResponse):
        """Process export request asynchronously."""
        try:
            # Update status to processing
            response.status = ExportStatus.PROCESSING
            await self._update_export_response(response)
            
            # Gather user data
            user_data = await self._gather_user_data(request)
            
            # Generate export file
            file_path = await self._generate_export_file(request, user_data)
            
            # Update response with completion details
            response.status = ExportStatus.COMPLETED
            response.completed_at = datetime.utcnow()
            response.file_size_bytes = os.path.getsize(file_path)
            response.download_url = f"/api/exports/{request.export_id}/download"
            response.progress_percentage = 100.0
            
            await self._update_export_response(response)
            
            # Update quota usage
            await self._update_export_quota(request.user_id)
            
            # Log completion
            await self._log_audit_event(request.user_id, "export_completed", request.export_id)
            
            # Send notification email if requested
            if request.email_when_ready:
                await self._send_export_notification(request.user_id, response)
                
        except Exception as e:
            logger.error(f"Error processing export {request.export_id}: {str(e)}")
            response.status = ExportStatus.FAILED
            response.error_message = str(e)
            await self._update_export_response(response)
    
    async def _gather_user_data(self, request: ExportRequest) -> Dict[str, Any]:
        """Gather user data based on requested categories."""
        user_data = {}
        
        try:
            # Load various data files
            data_files = {
                DataCategory.WATER_LOGS: "app/data/water_data.json",
                DataCategory.HEALTH_GOALS: "app/data/health_goals.json",
                DataCategory.ACHIEVEMENTS: "app/data/achievements.json",
                DataCategory.SOCIAL_DATA: "app/data/friendships.json",
                DataCategory.MESSAGES: "app/data/messages.json",
                DataCategory.ANALYTICS: "app/data/analytics_cache.json",
                DataCategory.PREFERENCES: "app/data/notification_settings.json"
            }
            
            for category in request.data_categories:
                if category in data_files:
                    file_path = Path(data_files[category])
                    if file_path.exists():
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            
                        # Filter by user_id and date range
                        filtered_data = self._filter_user_data(
                            data, request.user_id, 
                            request.date_range_start, request.date_range_end
                        )
                        user_data[category.value] = filtered_data
                
                # Handle profile data
                if category == DataCategory.PROFILE:
                    user_data[category.value] = await self._get_user_profile(request.user_id)
            
            return user_data
            
        except Exception as e:
            logger.error(f"Error gathering user data: {str(e)}")
            raise
    
    def _filter_user_data(self, data: List[Dict], user_id: int, 
                         start_date: Optional[date], end_date: Optional[date]) -> List[Dict]:
        """Filter data by user ID and date range."""
        filtered = []
        
        for item in data:
            # Filter by user_id
            if item.get('user_id') != user_id:
                continue
            
            # Filter by date range if specified
            if start_date or end_date:
                item_date = None
                for date_field in ['created_at', 'date', 'timestamp', 'logged_at']:
                    if date_field in item:
                        try:
                            item_date = datetime.fromisoformat(item[date_field].replace('Z', '+00:00')).date()
                            break
                        except:
                            continue
                
                if item_date:
                    if start_date and item_date < start_date:
                        continue
                    if end_date and item_date > end_date:
                        continue
            
            filtered.append(item)
        
        return filtered
    
    async def _generate_export_file(self, request: ExportRequest, user_data: Dict[str, Any]) -> str:
        """Generate export file in requested format."""
        export_data = ExportData(
            export_id=request.export_id,
            user_id=request.user_id,
            export_timestamp=datetime.utcnow(),
            data_categories=request.data_categories,
            date_range_start=request.date_range_start,
            date_range_end=request.date_range_end,
            data=user_data,
            metadata={
                "export_format": request.export_format.value,
                "privacy_level": request.privacy_level.value,
                "include_raw_data": request.include_raw_data,
                "include_analytics": request.include_analytics,
                "notes": request.notes
            },
            privacy_level=request.privacy_level,
            total_records=sum(len(v) if isinstance(v, list) else 1 for v in user_data.values()),
            file_format=request.export_format
        )
        
        # Generate file based on format
        if request.export_format == ExportFormat.JSON:
            return await self._generate_json_export(export_data)
        elif request.export_format == ExportFormat.CSV:
            return await self._generate_csv_export(export_data)
        elif request.export_format == ExportFormat.EXCEL:
            return await self._generate_excel_export(export_data)
        elif request.export_format == ExportFormat.PDF:
            return await self._generate_pdf_export(export_data)
        elif request.export_format == ExportFormat.XML:
            return await self._generate_xml_export(export_data)
        else:
            raise ValueError(f"Unsupported export format: {request.export_format}")
    
    async def _generate_json_export(self, export_data: ExportData) -> str:
        """Generate JSON export file."""
        file_path = self.export_dir / f"{export_data.export_id}.json"
        
        export_dict = {
            "export_metadata": {
                "export_id": export_data.export_id,
                "user_id": export_data.user_id,
                "export_timestamp": export_data.export_timestamp.isoformat(),
                "data_categories": [cat.value for cat in export_data.data_categories],
                "date_range_start": export_data.date_range_start.isoformat() if export_data.date_range_start else None,
                "date_range_end": export_data.date_range_end.isoformat() if export_data.date_range_end else None,
                "total_records": export_data.total_records,
                "privacy_level": export_data.privacy_level.value
            },
            "user_data": export_data.data,
            "metadata": export_data.metadata
        }
        
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(json.dumps(export_dict, indent=2, default=str))
        
        return str(file_path)
    
    async def _generate_csv_export(self, export_data: ExportData) -> str:
        """Generate CSV export file (creates ZIP with multiple CSV files)."""
        zip_path = self.export_dir / f"{export_data.export_id}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Create CSV for each data category
            for category, data in export_data.data.items():
                if isinstance(data, list) and data:
                    csv_buffer = io.StringIO()
                    
                    # Get field names from first record
                    fieldnames = list(data[0].keys()) if data else []
                    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)
                    
                    zipf.writestr(f"{category}.csv", csv_buffer.getvalue())
            
            # Add metadata file
            metadata_csv = io.StringIO()
            metadata_writer = csv.writer(metadata_csv)
            metadata_writer.writerow(["Key", "Value"])
            metadata_writer.writerow(["Export ID", export_data.export_id])
            metadata_writer.writerow(["User ID", export_data.user_id])
            metadata_writer.writerow(["Export Timestamp", export_data.export_timestamp.isoformat()])
            metadata_writer.writerow(["Total Records", export_data.total_records])
            metadata_writer.writerow(["Privacy Level", export_data.privacy_level.value])
            
            zipf.writestr("metadata.csv", metadata_csv.getvalue())
        
        return str(zip_path)
    
    async def _generate_excel_export(self, export_data: ExportData) -> str:
        """Generate Excel export file with multiple sheets."""
        file_path = self.export_dir / f"{export_data.export_id}.xlsx"
        
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # Create sheet for each data category
            for category, data in export_data.data.items():
                if isinstance(data, list) and data:
                    df = pd.DataFrame(data)
                    sheet_name = category.replace('_', ' ').title()[:31]  # Excel sheet name limit
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Add metadata sheet
            metadata_df = pd.DataFrame([
                {"Key": "Export ID", "Value": export_data.export_id},
                {"Key": "User ID", "Value": export_data.user_id},
                {"Key": "Export Timestamp", "Value": export_data.export_timestamp.isoformat()},
                {"Key": "Total Records", "Value": export_data.total_records},
                {"Key": "Privacy Level", "Value": export_data.privacy_level.value}
            ])
            metadata_df.to_excel(writer, sheet_name="Metadata", index=False)
        
        return str(file_path)
    
    async def _generate_pdf_export(self, export_data: ExportData) -> str:
        """Generate PDF export file."""
        file_path = self.export_dir / f"{export_data.export_id}.pdf"
        
        doc = SimpleDocTemplate(str(file_path), pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2196F3'),
            alignment=1  # Center alignment
        )
        story.append(Paragraph("Personal Data Export", title_style))
        story.append(Spacer(1, 12))
        
        # Metadata section
        story.append(Paragraph("Export Information", styles['Heading2']))
        metadata_data = [
            ["Export ID", export_data.export_id],
            ["User ID", str(export_data.user_id)],
            ["Export Date", export_data.export_timestamp.strftime("%Y-%m-%d %H:%M:%S")],
            ["Total Records", str(export_data.total_records)],
            ["Privacy Level", export_data.privacy_level.value.title()],
            ["Data Categories", ", ".join(cat.value.replace('_', ' ').title() for cat in export_data.data_categories)]
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(metadata_table)
        story.append(Spacer(1, 12))
        
        # Data sections
        for category, data in export_data.data.items():
            if isinstance(data, list) and data:
                story.append(Paragraph(category.replace('_', ' ').title(), styles['Heading2']))
                story.append(Paragraph(f"Total records: {len(data)}", styles['Normal']))
                story.append(Spacer(1, 6))
                
                # Show first few records as sample
                sample_data = data[:5]  # Show first 5 records
                if sample_data:
                    # Create table with first record's keys as headers
                    headers = list(sample_data[0].keys())[:5]  # Limit columns
                    table_data = [headers]
                    
                    for record in sample_data:
                        row = [str(record.get(header, ''))[:50] for header in headers]  # Limit cell content
                        table_data.append(row)
                    
                    data_table = Table(table_data)
                    data_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(data_table)
                    
                    if len(data) > 5:
                        story.append(Paragraph(f"... and {len(data) - 5} more records", styles['Italic']))
                
                story.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(story)
        return str(file_path)
    
    async def _generate_xml_export(self, export_data: ExportData) -> str:
        """Generate XML export file."""
        file_path = self.export_dir / f"{export_data.export_id}.xml"
        
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<export>
    <metadata>
        <export_id>{export_data.export_id}</export_id>
        <user_id>{export_data.user_id}</user_id>
        <export_timestamp>{export_data.export_timestamp.isoformat()}</export_timestamp>
        <total_records>{export_data.total_records}</total_records>
        <privacy_level>{export_data.privacy_level.value}</privacy_level>
    </metadata>
    <data>
"""
        
        for category, data in export_data.data.items():
            xml_content += f"        <{category}>\n"
            if isinstance(data, list):
                for item in data:
                    xml_content += "            <item>\n"
                    for key, value in item.items():
                        xml_content += f"                <{key}>{str(value)}</{key}>\n"
                    xml_content += "            </item>\n"
            xml_content += f"        </{category}>\n"
        
        xml_content += """    </data>
</export>"""
        
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(xml_content)
        
        return str(file_path)
    
    # GDPR and Privacy Methods
    
    async def create_gdpr_request(self, request: GDPRRequest) -> GDPRRequest:
        """Create a GDPR data request."""
        try:
            # Save GDPR request
            gdpr_requests = await self._load_gdpr_requests()
            gdpr_requests.append(request.dict())
            await self._save_gdpr_requests(gdpr_requests)
            
            # Log audit event
            await self._log_audit_event(request.user_id, "gdpr_request_created", request.request_id)
            
            # Process request based on type
            if request.request_type == "access":
                await self._process_gdpr_access_request(request)
            elif request.request_type == "portability":
                await self._process_gdpr_portability_request(request)
            elif request.request_type == "erasure":
                await self._process_gdpr_erasure_request(request)
            
            return request
            
        except Exception as e:
            logger.error(f"Error creating GDPR request: {str(e)}")
            raise
    
    async def _process_gdpr_access_request(self, request: GDPRRequest):
        """Process GDPR access request (Article 15)."""
        # Create comprehensive export with all user data
        export_request = ExportRequest(
            user_id=request.user_id,
            export_format=ExportFormat.JSON,
            data_categories=list(DataCategory),
            include_raw_data=True,
            include_analytics=True,
            privacy_level=PrivacyLevel.PRIVATE,
            notes=f"GDPR Access Request - {request.request_id}"
        )
        
        await self.create_export_request(export_request)
    
    async def _process_gdpr_portability_request(self, request: GDPRRequest):
        """Process GDPR portability request (Article 20)."""
        # Create machine-readable export
        export_request = ExportRequest(
            user_id=request.user_id,
            export_format=ExportFormat.JSON,
            data_categories=request.data_categories or list(DataCategory),
            include_raw_data=True,
            include_analytics=False,
            privacy_level=PrivacyLevel.PRIVATE,
            notes=f"GDPR Portability Request - {request.request_id}"
        )
        
        await self.create_export_request(export_request)
    
    # Utility Methods
    
    async def get_export_status(self, export_id: str) -> Optional[ExportResponse]:
        """Get export status by ID."""
        exports = await self._load_exports()
        for export in exports:
            if export.get('export_id') == export_id:
                return ExportResponse(**export)
        return None
    
    async def get_user_exports(self, user_id: int, page: int = 1, page_size: int = 10) -> List[ExportResponse]:
        """Get user's exports with pagination."""
        exports = await self._load_exports()
        user_exports = [ExportResponse(**exp) for exp in exports if exp.get('user_id') == user_id]
        
        # Sort by created_at descending
        user_exports.sort(key=lambda x: x.created_at, reverse=True)
        
        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        return user_exports[start:end]
    
    async def delete_export(self, export_id: str, user_id: int) -> bool:
        """Delete an export."""
        try:
            # Load exports
            exports = await self._load_exports()
            
            # Find and remove export
            for i, export in enumerate(exports):
                if export.get('export_id') == export_id and export.get('user_id') == user_id:
                    # Delete file
                    for ext in ['.json', '.csv', '.xlsx', '.pdf', '.xml', '.zip']:
                        file_path = self.export_dir / f"{export_id}{ext}"
                        if file_path.exists():
                            file_path.unlink()
                    
                    # Remove from list
                    exports.pop(i)
                    await self._save_exports(exports)
                    
                    # Log audit event
                    await self._log_audit_event(user_id, "export_deleted", export_id)
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting export: {str(e)}")
            return False
    
    async def _check_export_quota(self, user_id: int) -> bool:
        """Check if user has remaining export quota."""
        quotas = await self._load_quotas()
        user_quota = None
        
        for quota in quotas:
            if quota.get('user_id') == user_id:
                user_quota = ExportQuota(**quota)
                break
        
        if not user_quota:
            # Create default quota
            user_quota = ExportQuota(
                user_id=user_id,
                quota_reset_date=date.today() + timedelta(days=30)
            )
            quotas.append(user_quota.dict())
            await self._save_quotas(quotas)
        
        # Check daily limit
        if user_quota.daily_exports_used >= user_quota.daily_export_limit:
            return False
        
        # Check monthly limit
        if user_quota.monthly_exports_used >= user_quota.monthly_export_limit:
            return False
        
        return True
    
    async def _update_export_quota(self, user_id: int):
        """Update export quota usage."""
        quotas = await self._load_quotas()
        
        for quota in quotas:
            if quota.get('user_id') == user_id:
                quota['daily_exports_used'] = quota.get('daily_exports_used', 0) + 1
                quota['monthly_exports_used'] = quota.get('monthly_exports_used', 0) + 1
                break
        
        await self._save_quotas(quotas)
    
    # Data persistence methods
    
    async def _load_exports(self) -> List[Dict]:
        """Load exports from file."""
        if self.exports_file.exists():
            with open(self.exports_file, 'r') as f:
                return json.load(f)
        return []
    
    async def _save_exports(self, exports: List[Dict]):
        """Save exports to file."""
        with open(self.exports_file, 'w') as f:
            json.dump(exports, f, indent=2, default=str)
    
    async def _save_export_request(self, request: ExportRequest, response: ExportResponse):
        """Save export request and response."""
        exports = await self._load_exports()
        export_data = {
            "request": request.dict(),
            "response": response.dict()
        }
        exports.append(export_data)
        await self._save_exports(exports)
    
    async def _update_export_response(self, response: ExportResponse):
        """Update export response."""
        exports = await self._load_exports()
        
        for export in exports:
            if export.get('response', {}).get('export_id') == response.export_id:
                export['response'] = response.dict()
                break
        
        await self._save_exports(exports)
    
    async def _load_gdpr_requests(self) -> List[Dict]:
        """Load GDPR requests from file."""
        if self.gdpr_requests_file.exists():
            with open(self.gdpr_requests_file, 'r') as f:
                return json.load(f)
        return []
    
    async def _save_gdpr_requests(self, requests: List[Dict]):
        """Save GDPR requests to file."""
        with open(self.gdpr_requests_file, 'w') as f:
            json.dump(requests, f, indent=2, default=str)
    
    async def _load_quotas(self) -> List[Dict]:
        """Load export quotas from file."""
        if self.quotas_file.exists():
            with open(self.quotas_file, 'r') as f:
                return json.load(f)
        return []
    
    async def _save_quotas(self, quotas: List[Dict]):
        """Save export quotas to file."""
        with open(self.quotas_file, 'w') as f:
            json.dump(quotas, f, indent=2, default=str)
    
    async def _log_audit_event(self, user_id: int, action: str, export_id: Optional[str] = None):
        """Log audit event."""
        try:
            audit_logs = []
            if self.audit_logs_file.exists():
                with open(self.audit_logs_file, 'r') as f:
                    audit_logs = json.load(f)
            
            log_entry = ExportAuditLog(
                user_id=user_id,
                action=action,
                export_id=export_id
            )
            
            audit_logs.append(log_entry.dict())
            
            with open(self.audit_logs_file, 'w') as f:
                json.dump(audit_logs, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error logging audit event: {str(e)}")
    
    async def _get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Get user profile data."""
        # Mock user profile - in real implementation, this would query the user database
        return {
            "user_id": user_id,
            "username": f"user_{user_id}",
            "email": f"user_{user_id}@example.com",
            "created_at": "2024-01-01T00:00:00Z",
            "profile_data": {
                "name": f"User {user_id}",
                "age": 30,
                "gender": "prefer_not_to_say",
                "location": "Unknown"
            }
        }
    
    async def _send_export_notification(self, user_id: int, response: ExportResponse):
        """Send export completion notification."""
        # Mock notification - in real implementation, this would send email
        logger.info(f"Export {response.export_id} completed for user {user_id}")
    
    async def _count_pdf_pages(self, file_path: str) -> int:
        """Count pages in PDF file."""
        try:
            # Mock page count - in real implementation, use PyPDF2 or similar
            return 5
        except:
            return 1
    
    async def _generate_html_report(self, request: ReportRequest, report_data: ReportData) -> str:
        """Generate HTML report."""
        file_path = self.report_dir / f"{request.report_id}.html"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{request.title or 'Report'}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #2196F3; color: white; padding: 20px; }}
                .section {{ margin: 20px 0; }}
                .insight {{ background-color: #f0f8ff; padding: 10px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{request.title or 'Report'}</h1>
                <p>Generated on {report_data.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="section">
                <h2>Summary Statistics</h2>
                <ul>
        """
        
        for key, value in report_data.summary_statistics.items():
            html_content += f"<li><strong>{key.replace('_', ' ').title()}:</strong> {value}</li>"
        
        html_content += """
                </ul>
            </div>
            
            <div class="section">
                <h2>Key Insights</h2>
        """
        
        for insight in report_data.insights:
            html_content += f"""
                <div class="insight">
                    <h3>{insight['title']}</h3>
                    <p>{insight['description']}</p>
                </div>
            """
        
        html_content += """
            </div>
            
            <div class="section">
                <h2>Recommendations</h2>
                <ol>
        """
        
        for rec in report_data.recommendations:
            html_content += f"<li>{rec}</li>"
        
        html_content += """
                </ol>
            </div>
        </body>
        </html>
        """
        
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(html_content)
        
        return str(file_path)
    
    async def _generate_json_report(self, request: ReportRequest, report_data: ReportData) -> str:
        """Generate JSON report."""
        file_path = self.report_dir / f"{request.report_id}.json"
        
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(json.dumps(report_data.dict(), indent=2, default=str))
        
        return str(file_path)
    
    async def _load_reports(self) -> List[Dict]:
        """Load reports from file."""
        if self.reports_file.exists():
            with open(self.reports_file, 'r') as f:
                return json.load(f)
        return []
    
    async def _save_reports(self, reports: List[Dict]):
        """Save reports to file."""
        with open(self.reports_file, 'w') as f:
            json.dump(reports, f, indent=2, default=str)
    
    async def _save_report_request(self, request: ReportRequest, response: ReportResponse):
        """Save report request and response."""
        reports = await self._load_reports()
        report_data = {
            "request": request.dict(),
            "response": response.dict()
        }
        reports.append(report_data)
        await self._save_reports(reports)
    
    async def _update_report_response(self, response: ReportResponse):
        """Update report response."""
        reports = await self._load_reports()
        
        for report in reports:
            if report.get('response', {}).get('report_id') == response.report_id:
                report['response'] = response.dict()
                break
        
        await self._save_reports(reports) 