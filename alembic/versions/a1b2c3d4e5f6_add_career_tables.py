"""add career tables: resume, job_research, cover_letter

Revision ID: a1b2c3d4e5f6
Revises: 73bd178f36a6
Create Date: 2026-03-04

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'a1b2c3d4e5f6'
down_revision = '73bd178f36a6'
branch_labels = None
depends_on = None


def upgrade():
    # ── resume_profiles ───────────────────────────────────────────────────────
    op.create_table(
        'resume_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_resume_profiles_id'), 'resume_profiles', ['id'], unique=False)
    op.create_index(op.f('ix_resume_profiles_user_id'), 'resume_profiles', ['user_id'], unique=False)

    # ── resume_items ──────────────────────────────────────────────────────────
    item_category = sa.Enum(
        'experience', 'project', 'cert', 'activity', 'skill', 'education',
        name='itemcategory'
    )
    op.create_table(
        'resume_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('category', item_category, nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('organization', sa.String(length=300), nullable=True),
        sa.Column('start_date', sa.String(length=20), nullable=True),
        sa.Column('end_date', sa.String(length=20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['profile_id'], ['resume_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_resume_items_id'), 'resume_items', ['id'], unique=False)
    op.create_index(op.f('ix_resume_items_profile_id'), 'resume_items', ['profile_id'], unique=False)

    # ── saved_companies ───────────────────────────────────────────────────────
    op.create_table(
        'saved_companies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('company_name', sa.String(length=200), nullable=False),
        sa.Column('job_title', sa.String(length=300), nullable=True),
        sa.Column('source_url', sa.String(length=1000), nullable=True),
        sa.Column('raw_content', sa.Text(), nullable=True),
        sa.Column('analysis', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_saved_companies_id'), 'saved_companies', ['id'], unique=False)
    op.create_index(op.f('ix_saved_companies_user_id'), 'saved_companies', ['user_id'], unique=False)

    # ── cover_letters ─────────────────────────────────────────────────────────
    op.create_table(
        'cover_letters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('resume_profile_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['saved_companies.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['resume_profile_id'], ['resume_profiles.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_cover_letters_id'), 'cover_letters', ['id'], unique=False)
    op.create_index(op.f('ix_cover_letters_user_id'), 'cover_letters', ['user_id'], unique=False)

    # ── cover_letter_items ────────────────────────────────────────────────────
    op.create_table(
        'cover_letter_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cover_letter_id', sa.Integer(), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=True),
        sa.Column('char_limit', sa.Integer(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['cover_letter_id'], ['cover_letters.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_cover_letter_items_id'), 'cover_letter_items', ['id'], unique=False)
    op.create_index(op.f('ix_cover_letter_items_cover_letter_id'), 'cover_letter_items', ['cover_letter_id'], unique=False)


def downgrade():
    op.drop_table('cover_letter_items')
    op.drop_table('cover_letters')
    op.drop_table('saved_companies')
    op.drop_table('resume_items')
    op.drop_table('resume_profiles')
    sa.Enum(name='itemcategory').drop(op.get_bind(), checkfirst=True)
