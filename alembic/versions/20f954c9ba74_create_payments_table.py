"""Create payments table

Revision ID: 20f954c9ba74
Revises: 3178f8fa54b3
Create Date: 2025-04-08 18:31:25.282356

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20f954c9ba74'
down_revision = '3178f8fa54b3'
branch_labels = None
depends_on = None

def upgrade():
    # PaymentStatus enum 생성 부분 제거 (이미 존재함)
    
    # payments 테이블 생성
    op.create_table('payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('imp_uid', sa.String(), nullable=True),
        sa.Column('merchant_uid', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('status', sa.Enum('ready', 'paid', 'cancelled', 'failed', name='paymentstatus'), server_default='ready', nullable=False),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_id'), 'payments', ['id'], unique=False)
    op.create_index(op.f('ix_payments_imp_uid'), 'payments', ['imp_uid'], unique=True)
    op.create_index(op.f('ix_payments_merchant_uid'), 'payments', ['merchant_uid'], unique=True)

def downgrade():
    op.drop_index(op.f('ix_payments_merchant_uid'), table_name='payments')
    op.drop_index(op.f('ix_payments_imp_uid'), table_name='payments')
    op.drop_index(op.f('ix_payments_id'), table_name='payments')
    op.drop_table('payments')
