"""add event-related actions to pointactiontype

Revision ID: 73bd178f36a6
Revises: ccf9b3f60ce3
Create Date: 2025-05-25 08:41:06.498556

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '73bd178f36a6'
down_revision: Union[str, None] = 'f23019cd5fc9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE pointactiontype ADD VALUE IF NOT EXISTS 'signup_event'")
    op.execute("ALTER TYPE pointactiontype ADD VALUE IF NOT EXISTS 'invite_sent'")
    op.execute("ALTER TYPE pointactiontype ADD VALUE IF NOT EXISTS 'invite_used'")
    op.execute("ALTER TYPE pointactiontype ADD VALUE IF NOT EXISTS 'daily_login_event'")
    op.execute("ALTER TYPE pointactiontype ADD VALUE IF NOT EXISTS 'special_event'")


def downgrade() -> None:
    pass
