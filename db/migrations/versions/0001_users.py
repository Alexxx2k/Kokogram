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


def downgrade() -> None:
    op.drop_table("users")
