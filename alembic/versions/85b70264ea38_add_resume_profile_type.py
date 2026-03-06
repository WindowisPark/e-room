"""add_resume_profile_type

Revision ID: 85b70264ea38
Revises: 3eb97a66c727
Create Date: 2026-03-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '85b70264ea38'
down_revision: Union[str, None] = '3eb97a66c727'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ENUM 타입이 없을 경우에만 생성
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE profile_type_enum AS ENUM ('job', 'academic');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.add_column(
        'resume_profiles',
        sa.Column(
            'profile_type',
            sa.Enum('job', 'academic', name='profile_type_enum', create_type=False),
            server_default='job',
            nullable=False,
        )
    )


def downgrade() -> None:
    op.drop_column('resume_profiles', 'profile_type')
    op.execute("DROP TYPE IF EXISTS profile_type_enum")
