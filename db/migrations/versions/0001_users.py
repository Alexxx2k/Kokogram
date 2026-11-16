import sqlalchemy as sa
from alembic import op

revision = "0001_users"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
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
        sa.CheckConstraint(
            "email IS NOT NULL OR phone IS NOT NULL", name="ck_users_contact_present"
        ),
    )
    op.create_table(
        "sessions",
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
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_table(
        "contacts",
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("contact_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("owner_id", "contact_id", name="pk_contacts"),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["users.id"], name="fk_contacts_owner_id_users", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["contact_id"], ["users.id"], name="fk_contacts_contact_id_users", ondelete="CASCADE"
        ),
        sa.CheckConstraint("owner_id <> contact_id", name="ck_contacts_not_self"),
    )
    op.create_table(
        "blocks",
        sa.Column("blocker_id", sa.Uuid(), nullable=False),
        sa.Column("blocked_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("blocker_id", "blocked_id", name="pk_blocks"),
        sa.ForeignKeyConstraint(
            ["blocker_id"], ["users.id"], name="fk_blocks_blocker_id_users", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["blocked_id"], ["users.id"], name="fk_blocks_blocked_id_users", ondelete="CASCADE"
        ),
        sa.CheckConstraint("blocker_id <> blocked_id", name="ck_blocks_not_self"),
    )
    op.create_index("ix_blocks_blocked_id", "blocks", ["blocked_id"])


def downgrade() -> None:
    op.drop_index("ix_blocks_blocked_id", table_name="blocks")
    op.drop_table("blocks")
    op.drop_table("contacts")
    op.drop_index("ix_sessions_user_id", table_name="sessions")
    op.drop_table("sessions")
    op.drop_table("users")
