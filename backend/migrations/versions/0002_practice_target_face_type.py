"""practice target face type

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-20

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()

    # Guard against duplicate-column failures: branch commit 4ee4075 already
    # added this column via the old boot-time convergence code before this
    # migration existed, so any DB that ran that branch code (e.g. the
    # persistent db_dev_data volume) already has it despite having no
    # alembic_version table yet.
    existing = {column["name"] for column in sa.inspect(connection).get_columns("practices")}
    if "target_face_type" not in existing:
        op.add_column(
            "practices",
            sa.Column(
                "target_face_type",
                sa.String(length=20),
                nullable=False,
                server_default="compound",
            ),
        )

    # Still needed even when the column pre-exists: a pre-Alembic deployment
    # may have left rows with an empty-string value instead of the default.
    connection.execute(
        sa.text(
            "UPDATE practices "
            "SET target_face_type = 'compound' "
            "WHERE target_face_type IS NULL OR target_face_type = ''"
        )
    )


def downgrade():
    op.drop_column("practices", "target_face_type")
