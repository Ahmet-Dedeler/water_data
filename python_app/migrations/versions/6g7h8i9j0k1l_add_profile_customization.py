"""Add profile customization features

Revision ID: 6g7h8i9j0k1l
Revises: 5f6g7h8i9j0k
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6g7h8i9j0k1l'
down_revision = '5f6g7h8i9j0k'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to user_profiles table
    op.add_column('user_profiles', sa.Column('display_name', sa.String(100), nullable=True))
    op.add_column('user_profiles', sa.Column('bio', sa.Text(), nullable=True))
    op.add_column('user_profiles', sa.Column('avatar_style', sa.String(50), nullable=False, server_default='default'))
    op.add_column('user_profiles', sa.Column('avatar_config', sa.JSON(), nullable=True))
    op.add_column('user_profiles', sa.Column('theme_preference', sa.String(50), nullable=False, server_default='default'))
    op.add_column('user_profiles', sa.Column('privacy_settings', sa.JSON(), nullable=True))
    op.add_column('user_profiles', sa.Column('notification_preferences', sa.JSON(), nullable=True))
    op.add_column('user_profiles', sa.Column('social_links', sa.JSON(), nullable=True))
    op.add_column('user_profiles', sa.Column('location', sa.String(100), nullable=True))
    op.add_column('user_profiles', sa.Column('website', sa.String(255), nullable=True))
    op.add_column('user_profiles', sa.Column('interests', sa.JSON(), nullable=True))
    op.add_column('user_profiles', sa.Column('favorite_quotes', sa.JSON(), nullable=True))
    op.add_column('user_profiles', sa.Column('achievements_display', sa.JSON(), nullable=True))
    op.add_column('user_profiles', sa.Column('current_title_id', sa.Integer(), nullable=True))
    op.add_column('user_profiles', sa.Column('profile_views', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('user_profiles', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('user_profiles', sa.Column('verification_date', sa.DateTime(), nullable=True))
    op.add_column('user_profiles', sa.Column('moderation_notes', sa.Text(), nullable=True))
    
    # Create profile_badges table
    op.create_table('profile_badges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon_url', sa.String(255), nullable=True),
        sa.Column('color', sa.String(7), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('rarity', sa.String(20), nullable=False, server_default='common'),
        sa.Column('requirements', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_profile_badges_category', 'profile_badges', ['category'])
    op.create_index('ix_profile_badges_rarity', 'profile_badges', ['rarity'])
    
    # Create user_badges table
    op.create_table('user_badges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('badge_id', sa.Integer(), nullable=False),
        sa.Column('earned_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('is_displayed', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['badge_id'], ['profile_badges.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'badge_id')
    )
    op.create_index('ix_user_badges_user_id', 'user_badges', ['user_id'])
    op.create_index('ix_user_badges_badge_id', 'user_badges', ['badge_id'])
    
    # Create profile_themes table
    op.create_table('profile_themes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('preview_url', sa.String(255), nullable=True),
        sa.Column('theme_config', sa.JSON(), nullable=False),
        sa.Column('unlock_cost', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unlock_requirements', sa.JSON(), nullable=True),
        sa.Column('is_premium', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_profile_themes_is_premium', 'profile_themes', ['is_premium'])
    
    # Create user_themes table
    op.create_table('user_themes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('theme_id', sa.Integer(), nullable=False),
        sa.Column('unlocked_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('unlock_method', sa.String(50), nullable=True),
        sa.ForeignKeyConstraint(['theme_id'], ['profile_themes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'theme_id')
    )
    op.create_index('ix_user_themes_user_id', 'user_themes', ['user_id'])
    
    # Create avatar_assets table
    op.create_table('avatar_assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('asset_url', sa.String(255), nullable=False),
        sa.Column('unlock_cost', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unlock_requirements', sa.JSON(), nullable=True),
        sa.Column('rarity', sa.String(20), nullable=False, server_default='common'),
        sa.Column('is_premium', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_avatar_assets_category', 'avatar_assets', ['category'])
    op.create_index('ix_avatar_assets_rarity', 'avatar_assets', ['rarity'])
    
    # Create user_avatar_assets table
    op.create_table('user_avatar_assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.Column('unlocked_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('unlock_method', sa.String(50), nullable=True),
        sa.ForeignKeyConstraint(['asset_id'], ['avatar_assets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'asset_id')
    )
    op.create_index('ix_user_avatar_assets_user_id', 'user_avatar_assets', ['user_id'])
    
    # Create profile_customizations table
    op.create_table('profile_customizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('layout_style', sa.String(50), nullable=False, server_default='default'),
        sa.Column('color_scheme', sa.JSON(), nullable=True),
        sa.Column('widget_config', sa.JSON(), nullable=True),
        sa.Column('background_style', sa.String(50), nullable=True),
        sa.Column('animation_preferences', sa.JSON(), nullable=True),
        sa.Column('custom_css', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    # Create user_titles table
    op.create_table('user_titles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(7), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('rarity', sa.String(20), nullable=False, server_default='common'),
        sa.Column('unlock_requirements', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_titles_rarity', 'user_titles', ['rarity'])
    
    # Create user_title_ownership table
    op.create_table('user_title_ownership',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title_id', sa.Integer(), nullable=False),
        sa.Column('earned_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['title_id'], ['user_titles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'title_id')
    )
    op.create_index('ix_user_title_ownership_user_id', 'user_title_ownership', ['user_id'])
    
    # Create profile_showcases table
    op.create_table('profile_showcases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('featured_achievements', sa.JSON(), nullable=True),
        sa.Column('featured_stats', sa.JSON(), nullable=True),
        sa.Column('featured_badges', sa.JSON(), nullable=True),
        sa.Column('custom_sections', sa.JSON(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    # Create profile_visits table
    op.create_table('profile_visits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('visitor_id', sa.Integer(), nullable=False),
        sa.Column('profile_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['profile_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['visitor_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_profile_visits_visitor_id', 'profile_visits', ['visitor_id'])
    op.create_index('ix_profile_visits_profile_user_id', 'profile_visits', ['profile_user_id'])
    op.create_index('ix_profile_visits_created_at', 'profile_visits', ['created_at'])
    
    # Add foreign key constraint for current_title_id
    op.create_foreign_key('fk_user_profiles_current_title', 'user_profiles', 'user_titles', ['current_title_id'], ['id'])


def downgrade():
    # Drop foreign key constraint
    op.drop_constraint('fk_user_profiles_current_title', 'user_profiles', type_='foreignkey')
    
    # Drop tables in reverse order
    op.drop_table('profile_visits')
    op.drop_table('profile_showcases')
    op.drop_table('user_title_ownership')
    op.drop_table('user_titles')
    op.drop_table('profile_customizations')
    op.drop_table('user_avatar_assets')
    op.drop_table('avatar_assets')
    op.drop_table('user_themes')
    op.drop_table('profile_themes')
    op.drop_table('user_badges')
    op.drop_table('profile_badges')
    
    # Drop columns from user_profiles table
    op.drop_column('user_profiles', 'moderation_notes')
    op.drop_column('user_profiles', 'verification_date')
    op.drop_column('user_profiles', 'is_verified')
    op.drop_column('user_profiles', 'profile_views')
    op.drop_column('user_profiles', 'current_title_id')
    op.drop_column('user_profiles', 'achievements_display')
    op.drop_column('user_profiles', 'favorite_quotes')
    op.drop_column('user_profiles', 'interests')
    op.drop_column('user_profiles', 'website')
    op.drop_column('user_profiles', 'location')
    op.drop_column('user_profiles', 'social_links')
    op.drop_column('user_profiles', 'notification_preferences')
    op.drop_column('user_profiles', 'privacy_settings')
    op.drop_column('user_profiles', 'theme_preference')
    op.drop_column('user_profiles', 'avatar_config')
    op.drop_column('user_profiles', 'avatar_style')
    op.drop_column('user_profiles', 'bio')
    op.drop_column('user_profiles', 'display_name') 