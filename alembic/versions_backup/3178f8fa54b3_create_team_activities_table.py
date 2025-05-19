"""Create team_activities table

Revision ID: 3178f8fa54b3
Revises: ea30e9b05338
Create Date: 2025-04-05 20:59:48.303439

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '3178f8fa54b3'
down_revision = 'ea30e9b05338'
branch_labels = None
depends_on = None


def upgrade():
    # 1. PlanType enum 생성
    plantype = postgresql.ENUM('free', 'premium', 'vip', name='plantype')
    plantype.create(op.get_bind())

    # 2. User 모델에 구독 관련 필드 추가
    op.add_column('users', sa.Column('plan_type', sa.Enum('free', 'premium', 'vip', name='plantype'), nullable=False, server_default='free'))
    op.add_column('users', sa.Column('plan_started_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('plan_expires_at', sa.DateTime(), nullable=True))

    # 3. team_activities 테이블 생성
    op.create_table('team_activities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_team_activities_id'), 'team_activities', ['id'], unique=False)


def downgrade():
    # 1. team_activities 테이블 삭제
    op.drop_index(op.f('ix_team_activities_id'), table_name='team_activities')
    op.drop_table('team_activities')

    # 2. User 모델에서 구독 관련 필드 제거
    op.drop_column('users', 'plan_expires_at')
    op.drop_column('users', 'plan_started_at')
    op.drop_column('users', 'plan_type')

    # 3. PlanType enum 삭제
    op.execute('DROP TYPE plantype')