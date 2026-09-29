"""soft delete practice hierarchy

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-29
"""
from alembic import op
import sqlalchemy as sa


revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    for table in ("practices", "rounds", "ends"):
        op.add_column(table, sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.drop_column("rounds", "round_order")
    op.drop_column("ends", "end_number")


def downgrade():
    raise NotImplementedError("soft-delete markers and removed ordering cannot be restored safely")
