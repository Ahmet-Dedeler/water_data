"""Add water quality tracking

Revision ID: 8h9i0j1k2l3m
Revises: 6g7h8i9j0k1l
Create Date: 2024-01-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8h9i0j1k2l3m'
down_revision = '6g7h8i9j0k1l'
branch_labels = None
depends_on = None


def upgrade():
    # Create water_sources table
    op.create_table('water_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('type', sa.Enum('TAP', 'BOTTLED', 'FILTERED', 'WELL', 'SPRING', 'DISTILLED', 'SPARKLING', 'ALKALINE', 'REVERSE_OSMOSIS', 'UV_TREATED', name='watersourcetype'), nullable=False),
        sa.Column('brand', sa.String(length=100), nullable=True),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('ph_level', sa.Float(), nullable=True),
        sa.Column('tds_level', sa.Float(), nullable=True),
        sa.Column('hardness', sa.Float(), nullable=True),
        sa.Column('temperature_preference', sa.Float(), nullable=True),
        sa.Column('cost_per_liter', sa.Float(), nullable=True),
        sa.Column('last_tested', sa.DateTime(), nullable=True),
        sa.Column('next_test_due', sa.DateTime(), nullable=True),
        sa.Column('quality_rating', sa.Enum('EXCELLENT', 'GOOD', 'FAIR', 'POOR', 'UNKNOWN', name='waterqualityrating'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_water_sources_id'), 'water_sources', ['id'], unique=False)
    op.create_index(op.f('ix_water_sources_user_id'), 'water_sources', ['user_id'], unique=False)

    # Create water_quality_tests table
    op.create_table('water_quality_tests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('test_date', sa.DateTime(), nullable=False),
        sa.Column('test_type', sa.String(length=50), nullable=False),
        sa.Column('lab_name', sa.String(length=100), nullable=True),
        sa.Column('ph_level', sa.Float(), nullable=True),
        sa.Column('tds_level', sa.Float(), nullable=True),
        sa.Column('hardness', sa.Float(), nullable=True),
        sa.Column('chlorine_level', sa.Float(), nullable=True),
        sa.Column('fluoride_level', sa.Float(), nullable=True),
        sa.Column('lead_level', sa.Float(), nullable=True),
        sa.Column('bacteria_count', sa.Integer(), nullable=True),
        sa.Column('nitrate_level', sa.Float(), nullable=True),
        sa.Column('sulfate_level', sa.Float(), nullable=True),
        sa.Column('iron_level', sa.Float(), nullable=True),
        sa.Column('copper_level', sa.Float(), nullable=True),
        sa.Column('overall_rating', sa.Enum('EXCELLENT', 'GOOD', 'FAIR', 'POOR', 'UNKNOWN', name='waterqualityrating'), nullable=False),
        sa.Column('safety_score', sa.Integer(), nullable=True),
        sa.Column('taste_score', sa.Integer(), nullable=True),
        sa.Column('odor_score', sa.Integer(), nullable=True),
        sa.Column('clarity_score', sa.Integer(), nullable=True),
        sa.Column('test_results', sa.JSON(), nullable=True),
        sa.Column('recommendations', sa.Text(), nullable=True),
        sa.Column('issues_found', sa.JSON(), nullable=True),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('certified', sa.Boolean(), nullable=True),
        sa.Column('certificate_number', sa.String(length=100), nullable=True),
        sa.Column('expiry_date', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['water_sources.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_water_quality_tests_id'), 'water_quality_tests', ['id'], unique=False)
    op.create_index(op.f('ix_water_quality_tests_source_id'), 'water_quality_tests', ['source_id'], unique=False)
    op.create_index(op.f('ix_water_quality_tests_user_id'), 'water_quality_tests', ['user_id'], unique=False)

    # Create contamination_reports table
    op.create_table('contamination_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('contaminant_type', sa.Enum('CHLORINE', 'FLUORIDE', 'LEAD', 'BACTERIA', 'PESTICIDES', 'HEAVY_METALS', 'MICROPLASTICS', 'NITRATES', 'SULFATES', 'SEDIMENT', name='contaminanttype'), nullable=False),
        sa.Column('severity_level', sa.Integer(), nullable=False),
        sa.Column('detected_level', sa.Float(), nullable=True),
        sa.Column('safe_limit', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('detection_method', sa.String(length=100), nullable=True),
        sa.Column('symptoms_reported', sa.JSON(), nullable=True),
        sa.Column('action_taken', sa.Text(), nullable=True),
        sa.Column('resolved', sa.Boolean(), nullable=True),
        sa.Column('resolution_date', sa.DateTime(), nullable=True),
        sa.Column('location_details', sa.Text(), nullable=True),
        sa.Column('first_noticed', sa.DateTime(), nullable=True),
        sa.Column('last_observed', sa.DateTime(), nullable=True),
        sa.Column('verified_by_authority', sa.Boolean(), nullable=True),
        sa.Column('authority_name', sa.String(length=100), nullable=True),
        sa.Column('public_health_notified', sa.Boolean(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['water_sources.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contamination_reports_id'), 'contamination_reports', ['id'], unique=False)
    op.create_index(op.f('ix_contamination_reports_source_id'), 'contamination_reports', ['source_id'], unique=False)
    op.create_index(op.f('ix_contamination_reports_user_id'), 'contamination_reports', ['user_id'], unique=False)

    # Create water_quality_alerts table
    op.create_table('water_quality_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('trigger_data', sa.JSON(), nullable=True),
        sa.Column('threshold_exceeded', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('acknowledged', sa.Boolean(), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('resolved', sa.Boolean(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('notification_sent', sa.Boolean(), nullable=True),
        sa.Column('email_sent', sa.Boolean(), nullable=True),
        sa.Column('sms_sent', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['water_sources.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_water_quality_alerts_id'), 'water_quality_alerts', ['id'], unique=False)
    op.create_index(op.f('ix_water_quality_alerts_source_id'), 'water_quality_alerts', ['source_id'], unique=False)
    op.create_index(op.f('ix_water_quality_alerts_user_id'), 'water_quality_alerts', ['user_id'], unique=False)

    # Create water_filter_maintenance table
    op.create_table('water_filter_maintenance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('filter_type', sa.String(length=100), nullable=False),
        sa.Column('brand', sa.String(length=100), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('installation_date', sa.DateTime(), nullable=False),
        sa.Column('last_maintenance', sa.DateTime(), nullable=True),
        sa.Column('next_maintenance_due', sa.DateTime(), nullable=False),
        sa.Column('maintenance_frequency_days', sa.Integer(), nullable=False),
        sa.Column('filter_life_percentage', sa.Float(), nullable=True),
        sa.Column('gallons_filtered', sa.Float(), nullable=True),
        sa.Column('max_gallons', sa.Float(), nullable=True),
        sa.Column('maintenance_cost', sa.Float(), nullable=True),
        sa.Column('replacement_cost', sa.Float(), nullable=True),
        sa.Column('maintenance_notes', sa.Text(), nullable=True),
        sa.Column('low_life_alert_sent', sa.Boolean(), nullable=True),
        sa.Column('replacement_alert_sent', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['water_sources.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_water_filter_maintenance_id'), 'water_filter_maintenance', ['id'], unique=False)
    op.create_index(op.f('ix_water_filter_maintenance_source_id'), 'water_filter_maintenance', ['source_id'], unique=False)
    op.create_index(op.f('ix_water_filter_maintenance_user_id'), 'water_filter_maintenance', ['user_id'], unique=False)

    # Create water_quality_preferences table
    op.create_table('water_quality_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('preferred_ph_min', sa.Float(), nullable=True),
        sa.Column('preferred_ph_max', sa.Float(), nullable=True),
        sa.Column('preferred_tds_max', sa.Float(), nullable=True),
        sa.Column('preferred_hardness_max', sa.Float(), nullable=True),
        sa.Column('chlorine_sensitivity', sa.Boolean(), nullable=True),
        sa.Column('fluoride_preference', sa.String(length=20), nullable=True),
        sa.Column('temperature_preference', sa.Float(), nullable=True),
        sa.Column('test_reminder_frequency', sa.Integer(), nullable=True),
        sa.Column('quality_alert_threshold', sa.String(length=20), nullable=True),
        sa.Column('contamination_alerts', sa.Boolean(), nullable=True),
        sa.Column('filter_maintenance_alerts', sa.Boolean(), nullable=True),
        sa.Column('email_notifications', sa.Boolean(), nullable=True),
        sa.Column('sms_notifications', sa.Boolean(), nullable=True),
        sa.Column('push_notifications', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_water_quality_preferences_id'), 'water_quality_preferences', ['id'], unique=False)
    op.create_index(op.f('ix_water_quality_preferences_user_id'), 'water_quality_preferences', ['user_id'], unique=True)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_water_quality_preferences_user_id'), table_name='water_quality_preferences')
    op.drop_index(op.f('ix_water_quality_preferences_id'), table_name='water_quality_preferences')
    op.drop_table('water_quality_preferences')
    
    op.drop_index(op.f('ix_water_filter_maintenance_user_id'), table_name='water_filter_maintenance')
    op.drop_index(op.f('ix_water_filter_maintenance_source_id'), table_name='water_filter_maintenance')
    op.drop_index(op.f('ix_water_filter_maintenance_id'), table_name='water_filter_maintenance')
    op.drop_table('water_filter_maintenance')
    
    op.drop_index(op.f('ix_water_quality_alerts_user_id'), table_name='water_quality_alerts')
    op.drop_index(op.f('ix_water_quality_alerts_source_id'), table_name='water_quality_alerts')
    op.drop_index(op.f('ix_water_quality_alerts_id'), table_name='water_quality_alerts')
    op.drop_table('water_quality_alerts')
    
    op.drop_index(op.f('ix_contamination_reports_user_id'), table_name='contamination_reports')
    op.drop_index(op.f('ix_contamination_reports_source_id'), table_name='contamination_reports')
    op.drop_index(op.f('ix_contamination_reports_id'), table_name='contamination_reports')
    op.drop_table('contamination_reports')
    
    op.drop_index(op.f('ix_water_quality_tests_user_id'), table_name='water_quality_tests')
    op.drop_index(op.f('ix_water_quality_tests_source_id'), table_name='water_quality_tests')
    op.drop_index(op.f('ix_water_quality_tests_id'), table_name='water_quality_tests')
    op.drop_table('water_quality_tests')
    
    op.drop_index(op.f('ix_water_sources_user_id'), table_name='water_sources')
    op.drop_index(op.f('ix_water_sources_id'), table_name='water_sources')
    op.drop_table('water_sources')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS contaminanttype')
    op.execute('DROP TYPE IF EXISTS waterqualityrating')
    op.execute('DROP TYPE IF EXISTS watersourcetype') 