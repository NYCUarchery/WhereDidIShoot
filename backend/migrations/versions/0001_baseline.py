"""baseline

Revision ID: 0001
Revises:
Create Date: 2026-08-20

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def _sync_users_schema(connection, tables: set[str]) -> None:
    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("password", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        return

    inspector = sa.inspect(connection)
    user_columns = {column["name"] for column in inspector.get_columns("users")}

    if "password" not in user_columns and "password_hash" in user_columns:
        connection.execute(
            sa.text(
                "ALTER TABLE users CHANGE COLUMN password_hash password "
                "VARCHAR(255) NOT NULL DEFAULT ''"
            )
        )
        user_columns.remove("password_hash")
        user_columns.add("password")
    elif "password" not in user_columns:
        connection.execute(
            sa.text("ALTER TABLE users ADD COLUMN password VARCHAR(255) NOT NULL DEFAULT ''")
        )
        user_columns.add("password")

    if "password_hash" in user_columns:
        connection.execute(sa.text("ALTER TABLE users DROP COLUMN password_hash"))
        user_columns.remove("password_hash")

    if "email" in user_columns:
        connection.execute(sa.text("ALTER TABLE users DROP COLUMN email"))
        user_columns.remove("email")

    if "notes" in user_columns:
        connection.execute(sa.text("ALTER TABLE users DROP COLUMN notes"))
        user_columns.remove("notes")


def _sync_practices_schema(connection, tables: set[str]) -> None:
    if "practices" not in tables:
        op.create_table(
            "practices",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("distance_meters", sa.Integer(), nullable=False),
            sa.Column("target_face_cm", sa.Integer(), nullable=False),
            sa.Column("notes", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_practices_user_id"), "practices", ["user_id"], unique=False
        )
        return

    inspector = sa.inspect(connection)
    practice_columns = {column["name"] for column in inspector.get_columns("practices")}
    round_columns = (
        {column["name"] for column in inspector.get_columns("rounds")}
        if "rounds" in tables
        else set()
    )

    for column_name in ("title", "location", "practiced_on"):
        if column_name in practice_columns:
            connection.execute(sa.text(f"ALTER TABLE practices DROP COLUMN {column_name}"))
            practice_columns.remove(column_name)

    if "distance_meters" not in practice_columns:
        connection.execute(
            sa.text("ALTER TABLE practices ADD COLUMN distance_meters INTEGER NOT NULL DEFAULT 50")
        )
        practice_columns.add("distance_meters")

    if "target_face_cm" not in practice_columns:
        connection.execute(
            sa.text("ALTER TABLE practices ADD COLUMN target_face_cm INTEGER NOT NULL DEFAULT 80")
        )
        practice_columns.add("target_face_cm")

    if {"distance_meters", "target_face_cm"}.issubset(round_columns):
        practice_ids = connection.execute(
            sa.text("SELECT id FROM practices ORDER BY id ASC")
        ).scalars()

        for practice_id in practice_ids:
            round_settings = connection.execute(
                sa.text(
                    "SELECT distance_meters, target_face_cm "
                    "FROM rounds "
                    "WHERE practice_id = :practice_id "
                    "ORDER BY created_at ASC, id ASC "
                    "LIMIT 1"
                ),
                {"practice_id": practice_id},
            ).mappings().first()
            if round_settings is None:
                continue

            connection.execute(
                sa.text(
                    "UPDATE practices "
                    "SET distance_meters = :distance_meters, "
                    "target_face_cm = :target_face_cm "
                    "WHERE id = :practice_id"
                ),
                {
                    "practice_id": practice_id,
                    "distance_meters": int(round_settings["distance_meters"]),
                    "target_face_cm": int(round_settings["target_face_cm"]),
                },
            )


def _sync_rounds_schema(connection, tables: set[str]) -> None:
    if "rounds" not in tables:
        op.create_table(
            "rounds",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("practice_id", sa.Integer(), nullable=False),
            sa.Column("round_order", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=160), nullable=False),
            sa.Column("notes", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["practice_id"], ["practices.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_rounds_practice_id"), "rounds", ["practice_id"], unique=False
        )
        return

    inspector = sa.inspect(connection)
    round_columns = {column["name"] for column in inspector.get_columns("rounds")}

    if "round_order" not in round_columns:
        connection.execute(
            sa.text("ALTER TABLE rounds ADD COLUMN round_order INTEGER NOT NULL DEFAULT 0")
        )
        round_columns.add("round_order")

    # Renumber round_order per practice. This is a raw-SQL rewrite of the
    # legacy ORM-based renumbering (sync_rounds_schema in app/__init__.py);
    # migrations must not import app.models.
    practice_ids = connection.execute(
        sa.text("SELECT id FROM practices ORDER BY id ASC")
    ).scalars()

    for practice_id in practice_ids:
        round_ids = connection.execute(
            sa.text(
                "SELECT id FROM rounds "
                "WHERE practice_id = :practice_id "
                "ORDER BY created_at ASC, id ASC"
            ),
            {"practice_id": practice_id},
        ).scalars()

        for index, round_id in enumerate(round_ids, start=1):
            connection.execute(
                sa.text("UPDATE rounds SET round_order = :round_order WHERE id = :id"),
                {"round_order": index, "id": round_id},
            )

    for column_name in ("distance_meters", "target_face_cm"):
        if column_name in round_columns:
            connection.execute(sa.text(f"ALTER TABLE rounds DROP COLUMN {column_name}"))


def _sync_ends_schema(connection, tables: set[str]) -> None:
    if "ends" not in tables:
        op.create_table(
            "ends",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("round_id", sa.Integer(), nullable=False),
            sa.Column("end_number", sa.Integer(), nullable=False),
            sa.Column("notes", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["round_id"], ["rounds.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_ends_round_id"), "ends", ["round_id"], unique=False)
        return

    # No legacy convergence logic exists for `ends` in the pre-branch code;
    # the table shape has not changed across the tracked history.


def _sync_arrows_schema(connection, tables: set[str]) -> None:
    if "arrows" not in tables:
        op.create_table(
            "arrows",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("end_id", sa.Integer(), nullable=False),
            sa.Column("arrow_number", sa.Integer(), nullable=False),
            sa.Column("score", sa.Integer(), nullable=False),
            sa.Column("score_mark", sa.String(length=1), nullable=False),
            sa.Column("x", sa.Float(), nullable=False),
            sa.Column("y", sa.Float(), nullable=False),
            sa.Column("notes", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["end_id"], ["ends.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_arrows_end_id"), "arrows", ["end_id"], unique=False)
        return

    inspector = sa.inspect(connection)
    arrow_columns = {column["name"] for column in inspector.get_columns("arrows")}

    if "score_mark" not in arrow_columns:
        connection.execute(
            sa.text("ALTER TABLE arrows ADD COLUMN score_mark VARCHAR(1) NOT NULL DEFAULT ''")
        )
        arrow_columns.add("score_mark")

    connection.execute(
        sa.text(
            "UPDATE arrows "
            "SET score_mark = 'M' "
            "WHERE score = 0 AND (score_mark IS NULL OR score_mark = '')"
        )
    )

    # 2.339 is the value of INNER_TEN_SCORE_RADIUS_CM (backend/app/routes.py)
    # frozen at this revision. Migrations must not import application code.
    inner_ten_score_radius_cm = 2.339
    connection.execute(
        sa.text(
            "UPDATE arrows "
            "SET score_mark = 'X' "
            "WHERE score = 10 "
            "AND SQRT(POW(x, 2) + POW(y, 2)) <= :inner_ten_score_radius_cm "
            "AND (score_mark IS NULL OR score_mark = '')"
        ),
        {"inner_ten_score_radius_cm": inner_ten_score_radius_cm},
    )


def upgrade():
    connection = op.get_bind()

    tables = set(sa.inspect(connection).get_table_names())
    _sync_users_schema(connection, tables)

    tables = set(sa.inspect(connection).get_table_names())
    _sync_practices_schema(connection, tables)

    tables = set(sa.inspect(connection).get_table_names())
    _sync_rounds_schema(connection, tables)

    tables = set(sa.inspect(connection).get_table_names())
    _sync_ends_schema(connection, tables)

    tables = set(sa.inspect(connection).get_table_names())
    _sync_arrows_schema(connection, tables)


def downgrade():
    raise NotImplementedError("0001 is the baseline revision; downgrade is not supported.")
