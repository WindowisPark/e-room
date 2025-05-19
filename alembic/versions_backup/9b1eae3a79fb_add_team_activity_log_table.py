"""add team activity log table

Revision ID: 9b1eae3a79fb
Revises: ae01e8831db3
Create Date: 2025-04-02 00:13:42.464899

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9b1eae3a79fb'
down_revision: Union[str, None] = 'ae01e8831db3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'team_activities',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('team_id', sa.Integer(), sa.ForeignKey("teams.id", ondelete="CASCADE")),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    # 오류 방지를 위해 기존 payments 테이블 관련 제거 생략
    pass
