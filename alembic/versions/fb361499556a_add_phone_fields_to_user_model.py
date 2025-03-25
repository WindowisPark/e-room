"""add phone fields to user model

Revision ID: fb361499556a
Revises: 8624e9dc7c5b
Create Date: 2025-03-14 17:21:24.689484

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fb361499556a'
down_revision: Union[str, None] = '8624e9dc7c5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 사용자 테이블에 전화번호 관련 필드 추가
    op.add_column('users', sa.Column('phone_number', sa.String(), nullable=True))
    op.add_column('users', sa.Column('is_phone_verified', sa.Boolean(), server_default='false', nullable=False))


def downgrade() -> None:
    # 롤백 시 추가한 컬럼 제거
    op.drop_column('users', 'is_phone_verified')
    op.drop_column('users', 'phone_number')
