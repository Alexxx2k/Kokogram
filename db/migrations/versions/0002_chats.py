import sqlalchemy as sa
from alembic import op

revision = "0002_chats"
down_revision = "0001_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chats",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(8), nullable=False),
        sa.Column("title", sa.String(20), nullable=True),
        sa.Column("avatar_key", sa.String(255), nullable=True),
        sa.Column("direct_key", sa.String(73), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_chats"),
        sa.UniqueConstraint("direct_key", name="uq_chats_direct_key"),
        sa.CheckConstraint("type IN ('personal', 'group')", name="ck_chats_type"),
        sa.CheckConstraint(
            "type <> 'group' OR "
            "(title IS NOT NULL AND char_length(title) >= 1 AND direct_key IS NULL)",
            name="ck_chats_group_fields",
        ),
        sa.CheckConstraint(
            "type <> 'personal' OR (title IS NULL AND direct_key IS NOT NULL)",
            name="ck_chats_personal_fields",
        ),
    )
    op.create_table(
        "chat_members",
        sa.Column("chat_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(6), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_read_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("chat_id", "user_id", name="pk_chat_members"),
        sa.ForeignKeyConstraint(
            ["chat_id"], ["chats.id"], name="fk_chat_members_chat_id_chats", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_chat_members_user_id_users", ondelete="CASCADE"
        ),
        sa.CheckConstraint("role IN ('owner', 'admin', 'member')", name="ck_chat_members_role"),
    )
    op.create_index("ix_chat_members_user_id", "chat_members", ["user_id"])
    op.execute(
        "CREATE UNIQUE INDEX uq_chat_members_owner ON chat_members (chat_id) WHERE role = 'owner'"
    )


def downgrade() -> None:
    op.drop_index("uq_chat_members_owner", table_name="chat_members")
    op.drop_index("ix_chat_members_user_id", table_name="chat_members")
    op.drop_table("chat_members")
    op.drop_table("chats")
