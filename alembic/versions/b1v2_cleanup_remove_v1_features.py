"""v2 cleanup: remove teams/gamification/payments, add career tables

Revision ID: b1v2cleanup001
Revises: 20f954c9ba74
Create Date: 2026-03-04

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'b1v2cleanup001'
down_revision = '20f954c9ba74'
branch_labels = None
depends_on = None


def upgrade():
    # ── 1. pdf_files.team_id FK + 컬럼 먼저 제거 (teams 테이블 의존) ─────────
    op.execute("""
        DO $$
        DECLARE r record;
        BEGIN
            FOR r IN SELECT constraint_name FROM information_schema.table_constraints
                     WHERE table_name='pdf_files' AND constraint_type='FOREIGN KEY'
                       AND constraint_name ILIKE '%team%'
            LOOP
                EXECUTE 'ALTER TABLE pdf_files DROP CONSTRAINT ' || r.constraint_name;
            END LOOP;
        END$$;
    """)
    op.drop_column('pdf_files', 'team_id')

    # ── 2. 외래키 의존 순서로 테이블 삭제 ─────────────────────────────────────

    # mentions (→ tags, users)
    op.drop_table('mentions')

    # gamification (→ users, badges)
    op.drop_table('point_history')
    op.drop_table('user_badges')
    op.drop_table('badges')

    # team (→ users) — pdf_files FK 제거 후 삭제 가능
    op.drop_table('team_activities')
    op.drop_table('team_members')
    op.drop_table('teams')

    # 기타 (→ users)
    op.drop_table('payments')
    op.drop_table('notifications')
    op.drop_table('questions')
    op.drop_table('attendance')

    # ── 3. users 컬럼 제거 ─────────────────────────────────────────────────────
    op.drop_column('users', 'phone_number')
    op.drop_column('users', 'is_phone_verified')
    op.drop_column('users', 'allow_mention_notifications')
    op.drop_column('users', 'plan_type')
    op.drop_column('users', 'plan_started_at')
    op.drop_column('users', 'plan_expires_at')
    op.drop_column('users', 'points')
    op.drop_column('users', 'level')
    op.drop_column('users', 'streak_days')
    op.drop_column('users', 'exp')

    # ── 4. 사용하지 않는 enum 타입 삭제 ──────────────────────────────────────
    op.execute("DROP TYPE IF EXISTS plantype CASCADE")
    op.execute("DROP TYPE IF EXISTS paymentstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS team_role_enum CASCADE")
    op.execute("DROP TYPE IF EXISTS pointactiontype CASCADE")
    op.execute("DROP TYPE IF EXISTS badgetype CASCADE")

    # ── 5. password_reset_tokens 테이블 생성 ──────────────────────────────────
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token'),
    )
    op.create_index(op.f('ix_password_reset_tokens_id'), 'password_reset_tokens', ['id'], unique=False)
    op.create_index(op.f('ix_password_reset_tokens_token'), 'password_reset_tokens', ['token'], unique=True)

    # ── 6. 취업 준비 테이블 생성 ──────────────────────────────────────────────

    # resume_profiles
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

    # resume_items
    item_category_enum = sa.Enum(
        'experience', 'project', 'cert', 'activity', 'skill', 'education',
        name='itemcategory'
    )
    op.create_table(
        'resume_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('category', item_category_enum, nullable=False),
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

    # saved_companies
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

    # cover_letters
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

    # cover_letter_items
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
    # career tables
    op.drop_table('cover_letter_items')
    op.drop_table('cover_letters')
    op.drop_table('saved_companies')
    op.drop_table('resume_items')
    op.drop_table('resume_profiles')
    sa.Enum(name='itemcategory').drop(op.get_bind(), checkfirst=True)

    op.drop_table('password_reset_tokens')

    # NOTE: downgrade는 v1 테이블/컬럼 복구를 하지 않습니다.
    # v1 상태로 되돌리려면 데이터베이스 백업을 사용하세요.
    raise NotImplementedError("v2 → v1 downgrade는 지원하지 않습니다. DB 백업을 사용하세요.")
