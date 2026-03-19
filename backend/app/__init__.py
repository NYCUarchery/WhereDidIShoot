from flask import Flask
from sqlalchemy import inspect, text

from .config import Config
from .extensions import db
from . import models
from .routes import INNER_TEN_SCORE_RADIUS_CM, api


def sync_users_schema() -> None:
    inspector = inspect(db.engine)
    table_names = set(inspector.get_table_names())
    if "users" not in table_names:
        return

    user_columns = {column["name"] for column in inspector.get_columns("users")}

    with db.engine.begin() as connection:
        if "password" not in user_columns and "password_hash" in user_columns:
            connection.execute(
                text(
                    "ALTER TABLE users CHANGE COLUMN password_hash password "
                    "VARCHAR(255) NOT NULL DEFAULT ''"
                )
            )
            user_columns.remove("password_hash")
            user_columns.add("password")
        elif "password" not in user_columns:
            connection.execute(
                text("ALTER TABLE users ADD COLUMN password VARCHAR(255) NOT NULL DEFAULT ''")
            )
            user_columns.add("password")

        if "password_hash" in user_columns:
            connection.execute(text("ALTER TABLE users DROP COLUMN password_hash"))
            user_columns.remove("password_hash")

        if "email" in user_columns:
            connection.execute(text("ALTER TABLE users DROP COLUMN email"))
            user_columns.remove("email")

        if "notes" in user_columns:
            connection.execute(text("ALTER TABLE users DROP COLUMN notes"))
            user_columns.remove("notes")


def sync_practices_schema() -> None:
    inspector = inspect(db.engine)
    table_names = set(inspector.get_table_names())
    if "practices" not in table_names:
        return

    practice_columns = {column["name"] for column in inspector.get_columns("practices")}
    round_columns = (
        {column["name"] for column in inspector.get_columns("rounds")}
        if "rounds" in table_names
        else set()
    )

    with db.engine.begin() as connection:
        for column_name in ("title", "location", "practiced_on"):
            if column_name in practice_columns:
                connection.execute(text(f"ALTER TABLE practices DROP COLUMN {column_name}"))
                practice_columns.remove(column_name)

        if "distance_meters" not in practice_columns:
            connection.execute(
                text("ALTER TABLE practices ADD COLUMN distance_meters INTEGER NOT NULL DEFAULT 50")
            )
            practice_columns.add("distance_meters")

        if "target_face_cm" not in practice_columns:
            connection.execute(
                text("ALTER TABLE practices ADD COLUMN target_face_cm INTEGER NOT NULL DEFAULT 80")
            )
            practice_columns.add("target_face_cm")

        if {"distance_meters", "target_face_cm"}.issubset(round_columns):
            practice_ids = connection.execute(
                text("SELECT id FROM practices ORDER BY id ASC")
            ).scalars()

            for practice_id in practice_ids:
                round_settings = connection.execute(
                    text(
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
                    text(
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


def sync_rounds_schema() -> None:
    inspector = inspect(db.engine)
    table_names = set(inspector.get_table_names())
    if "rounds" not in table_names:
        return

    round_columns = {column["name"] for column in inspector.get_columns("rounds")}

    with db.engine.begin() as connection:
        if "round_order" not in round_columns:
            connection.execute(
                text("ALTER TABLE rounds ADD COLUMN round_order INTEGER NOT NULL DEFAULT 0")
            )
            round_columns.add("round_order")

    practices = models.Practice.query.order_by(models.Practice.id.asc()).all()
    for practice in practices:
        rounds = (
            models.Round.query.filter(models.Round.practice_id == practice.id)
            .order_by(models.Round.created_at.asc(), models.Round.id.asc())
            .all()
        )

        for index, round_record in enumerate(rounds, start=1):
            round_record.round_order = index

    db.session.commit()

    with db.engine.begin() as connection:
        for column_name in ("distance_meters", "target_face_cm"):
            if column_name in round_columns:
                connection.execute(text(f"ALTER TABLE rounds DROP COLUMN {column_name}"))


def sync_arrows_schema() -> None:
    inspector = inspect(db.engine)
    table_names = set(inspector.get_table_names())
    if "arrows" not in table_names:
        return

    arrow_columns = {column["name"] for column in inspector.get_columns("arrows")}

    with db.engine.begin() as connection:
        if "score_mark" not in arrow_columns:
            connection.execute(
                text("ALTER TABLE arrows ADD COLUMN score_mark VARCHAR(1) NOT NULL DEFAULT ''")
            )
            arrow_columns.add("score_mark")

        connection.execute(
            text(
                "UPDATE arrows "
                "SET score_mark = 'M' "
                "WHERE score = 0 AND (score_mark IS NULL OR score_mark = '')"
            )
        )
        connection.execute(
            text(
                "UPDATE arrows "
                "SET score_mark = 'X' "
                "WHERE score = 10 "
                "AND SQRT(POW(x, 2) + POW(y, 2)) <= :inner_ten_score_radius_cm "
                "AND (score_mark IS NULL OR score_mark = '')"
            ),
            {"inner_ten_score_radius_cm": INNER_TEN_SCORE_RADIUS_CM},
        )


def ensure_schema() -> None:
    sync_users_schema()
    sync_practices_schema()
    sync_rounds_schema()
    sync_arrows_schema()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    app.register_blueprint(api)

    with app.app_context():
        db.create_all()
        ensure_schema()

    return app
