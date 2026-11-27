import sqlalchemy as sa

metadata = sa.MetaData()

# Описания соответствуют 0001_users; схему создают только миграции Alembic.
users = sa.Table(
    "users",
    metadata,
    sa.Column("id", sa.Uuid(), nullable=False),
    sa.Column("email", sa.String(254), nullable=True),
    sa.Column("phone", sa.String(16), nullable=True),
    sa.Column("password_hash", sa.String(255), nullable=False),
    sa.Column("username", sa.String(12), nullable=False),
    sa.Column("status", sa.String(20), nullable=True),
    sa.Column("avatar_key", sa.String(255), nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint("id", name="pk_users"),
    sa.UniqueConstraint("email", name="uq_users_email"),
    sa.UniqueConstraint("phone", name="uq_users_phone"),
    sa.UniqueConstraint("username", name="uq_users_username"),
    sa.CheckConstraint("email IS NOT NULL OR phone IS NOT NULL", name="ck_users_contact_present"),
)

sessions = sa.Table(
    "sessions",
    metadata,
    sa.Column("id", sa.Uuid(), nullable=False),
    sa.Column("user_id", sa.Uuid(), nullable=False),
    sa.Column("token_hash", sa.String(255), nullable=False),
    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint("id", name="pk_sessions"),
    sa.UniqueConstraint("token_hash", name="uq_sessions_token_hash"),
    sa.ForeignKeyConstraint(
        ["user_id"], ["users.id"], name="fk_sessions_user_id_users", ondelete="CASCADE"
    ),
)
sa.Index("ix_sessions_user_id", sessions.c.user_id)
