"""add intelligence metrics to leads table

Revision ID: a1b2c3d4e5f6
Revises: previous_revision
Create Date: 2026-08-05 21:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('leads', sa.Column('lead_score', sa.Integer(), server_default='0', nullable=False))
    op.add_column('leads', sa.Column('lead_priority', sa.String(length=20), server_default='LOW', nullable=False))
    op.add_column('leads', sa.Column('seo_score', sa.Integer(), server_default='0', nullable=False))
    op.add_column('leads', sa.Column('email_status', sa.String(length=30), server_default='UNKNOWN', nullable=False))
    op.add_column('leads', sa.Column('ssl_enabled', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('leads', sa.Column('mobile_friendly', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('leads', sa.Column('page_speed', sa.Integer(), server_default='0', nullable=False))
    op.add_column('leads', sa.Column('meta_title', sa.Text(), nullable=True))
    op.add_column('leads', sa.Column('meta_description', sa.Text(), nullable=True))
    op.add_column('leads', sa.Column('robots_found', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('leads', sa.Column('sitemap_found', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('leads', sa.Column('schema_found', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('leads', sa.Column('domain_age', sa.Integer(), server_default='0', nullable=True))
    op.add_column('leads', sa.Column('ai_summary', sa.Text(), nullable=True))
    op.add_column('leads', sa.Column('last_audit_at', sa.DateTime(timezone=True), nullable=True))

def downgrade():
    op.drop_column('leads', 'last_audit_at')
    op.drop_column('leads', 'ai_summary')
    op.drop_column('leads', 'domain_age')
    op.drop_column('leads', 'schema_found')
    op.drop_column('leads', 'sitemap_found')
    op.drop_column('leads', 'robots_found')
    op.drop_column('leads', 'meta_description')
    op.drop_column('leads', 'meta_title')
    op.drop_column('leads', 'page_speed')
    op.drop_column('leads', 'mobile_friendly')
    op.drop_column('leads', 'ssl_enabled')
    op.drop_column('leads', 'email_status')
    op.drop_column('leads', 'seo_score')
    op.drop_column('leads', 'lead_priority')
    op.drop_column('leads', 'lead_score')
