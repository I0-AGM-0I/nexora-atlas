"""add_resource_metric_observations

Revision ID: 6c2e3f8d9b1a
Revises: 4b0cbd317c07
Create Date: 2026-09-18 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6c2e3f8d9b1a'
down_revision: Union[str, None] = '4b0cbd317c07'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'resource_metric_observations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('cloud_account_id', sa.String(length=36), nullable=False),
        sa.Column('resource_id', sa.String(length=36), nullable=False),
        sa.Column('source_observation_key', sa.String(length=64), nullable=False),
        sa.Column('provider_type', sa.String(length=50), nullable=False),
        sa.Column('metric_namespace', sa.String(length=100), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('source_statistic', sa.String(length=50), nullable=False),
        sa.Column('period_seconds', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('value', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.Column('dimensions_json', sa.JSON(), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('retrieved_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sync_job_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['cloud_account_id'], ['cloud_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resource_id'], ['cloud_resources.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sync_job_id'], ['sync_jobs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_observation_key', name='uq_telemetry_source_observation_key')
    )
    op.create_index(op.f('ix_resource_metric_observations_id'), 'resource_metric_observations', ['id'], unique=False)
    op.create_index(op.f('ix_resource_metric_observations_organization_id'), 'resource_metric_observations', ['organization_id'], unique=False)
    op.create_index(op.f('ix_resource_metric_observations_cloud_account_id'), 'resource_metric_observations', ['cloud_account_id'], unique=False)
    op.create_index(op.f('ix_resource_metric_observations_resource_id'), 'resource_metric_observations', ['resource_id'], unique=False)
    op.create_index(op.f('ix_resource_metric_observations_source_observation_key'), 'resource_metric_observations', ['source_observation_key'], unique=True)
    op.create_index('ix_telemetry_resource_metric_ts', 'resource_metric_observations', ['resource_id', 'metric_name', 'timestamp'], unique=False)
    op.create_index('ix_telemetry_account_metric_ts', 'resource_metric_observations', ['cloud_account_id', 'metric_name', 'timestamp'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_telemetry_account_metric_ts', table_name='resource_metric_observations')
    op.drop_index('ix_telemetry_resource_metric_ts', table_name='resource_metric_observations')
    op.drop_index(op.f('ix_resource_metric_observations_source_observation_key'), table_name='resource_metric_observations')
    op.drop_index(op.f('ix_resource_metric_observations_resource_id'), table_name='resource_metric_observations')
    op.drop_index(op.f('ix_resource_metric_observations_cloud_account_id'), table_name='resource_metric_observations')
    op.drop_index(op.f('ix_resource_metric_observations_organization_id'), table_name='resource_metric_observations')
    op.drop_index(op.f('ix_resource_metric_observations_id'), table_name='resource_metric_observations')
    op.drop_table('resource_metric_observations')
