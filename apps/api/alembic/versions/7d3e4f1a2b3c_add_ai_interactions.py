"""add_ai_interactions

Revision ID: 7d3e4f1a2b3c
Revises: 6c2e3f8d9b1a
Create Date: 2026-09-18 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d3e4f1a2b3c'
down_revision: Union[str, None] = '6c2e3f8d9b1a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_interactions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('question', sa.String(length=2000), nullable=False),
        sa.Column('question_category', sa.String(length=50), nullable=False),
        sa.Column('scope_type', sa.String(length=50), nullable=False),
        sa.Column('scope_id', sa.String(length=255), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('prompt_version', sa.String(length=50), nullable=False),
        sa.Column('context_version', sa.String(length=50), nullable=False),
        sa.Column('evidence_hash', sa.String(length=64), nullable=False),
        sa.Column('evidence_ids', sa.JSON(), nullable=False),
        sa.Column('response_status', sa.String(length=50), nullable=False),
        sa.Column('answer_json', sa.JSON(), nullable=True),
        sa.Column('sanitized_evidence_preview', sa.JSON(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=False),
        sa.Column('input_token_count', sa.Integer(), nullable=False),
        sa.Column('output_token_count', sa.Integer(), nullable=False),
        sa.Column('estimated_cost_usd', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('evidence_count', sa.Integer(), nullable=False),
        sa.Column('error_code', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_interactions_id'), 'ai_interactions', ['id'], unique=False)
    op.create_index(op.f('ix_ai_interactions_organization_id'), 'ai_interactions', ['organization_id'], unique=False)
    op.create_index(op.f('ix_ai_interactions_session_id'), 'ai_interactions', ['session_id'], unique=False)
    op.create_index(op.f('ix_ai_interactions_evidence_hash'), 'ai_interactions', ['evidence_hash'], unique=False)
    op.create_index('idx_ai_interaction_org_created', 'ai_interactions', ['organization_id', 'created_at'], unique=False)
    op.create_index('idx_ai_interaction_session_created', 'ai_interactions', ['session_id', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_ai_interaction_session_created', table_name='ai_interactions')
    op.drop_index('idx_ai_interaction_org_created', table_name='ai_interactions')
    op.drop_index(op.f('ix_ai_interactions_evidence_hash'), table_name='ai_interactions')
    op.drop_index(op.f('ix_ai_interactions_session_id'), table_name='ai_interactions')
    op.drop_index(op.f('ix_ai_interactions_organization_id'), table_name='ai_interactions')
    op.drop_index(op.f('ix_ai_interactions_id'), table_name='ai_interactions')
    op.drop_table('ai_interactions')
