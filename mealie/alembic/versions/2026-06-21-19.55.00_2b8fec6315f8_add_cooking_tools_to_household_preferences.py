"""add cooking tools to household preferences

Revision ID: 2b8fec6315f8
Revises: 2187537c52b8
Create Date: 2026-06-21 195500

"""
import sqlalchemy as sa
from alembic import op

revision = "2b8fec6315f8"
down_revision: str | None = "2187537c52b8"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade():
    with op.batch_alter_table("household_preferences", schema=None) as batch_op:
        batch_op.add_column(sa.Column("cooking_tools", sa.String(), nullable=True, server_default='[]'))


def downgrade():
    with op.batch_alter_table("household_preferences", schema=None) as batch_op:
        batch_op.drop_column("cooking_tools")
