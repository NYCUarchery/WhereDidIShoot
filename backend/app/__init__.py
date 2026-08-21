import os
from pathlib import Path

from flask import Flask
from flask_migrate import Migrate, upgrade

from .config import Config
from .extensions import db
from .routes import api

# Registering models with SQLAlchemy's metadata is a required import side
# effect: without it, `target_metadata` (used by Alembic autogenerate) would
# not know about any of the ORM-mapped tables.
from . import models  # noqa: F401

MIGRATIONS_DIR = str(Path(__file__).resolve().parent.parent / "migrations")

migrate = Migrate()


def _run_db_upgrade_enabled() -> bool:
    # Repair escape hatch: FLASK_APP=wsgi:app makes every `flask db ...`
    # subcommand go through create_app(), which normally runs the boot-time
    # upgrade first. If a migration is broken, that means `flask db current`,
    # `flask db history`, and `flask db stamp` all fail the same way as the
    # app itself, leaving an operator with no way to inspect or repair state.
    # Set RUN_DB_UPGRADE=0/false/no to skip the upgrade and get a working
    # shell for those subcommands.
    return os.getenv("RUN_DB_UPGRADE", "1").strip().lower() not in ("0", "false", "no")


def _upgrade_database() -> None:
    engine = db.engine
    if engine.dialect.name != "mysql":
        upgrade(directory=MIGRATIONS_DIR)
        return

    # GET_LOCK is scoped to the connection that acquired it, so the lock must
    # be held on this same connection for the whole upgrade. This guards
    # against the race between the two gunicorn workers (see
    # backend/gunicorn.conf.py, workers = 2, no preload_app) both booting and
    # attempting to run migrations concurrently.
    #
    # The wait per attempt (and the total across retries) must stay well
    # under gunicorn.conf.py's `timeout = 60`: gunicorn's arbiter kills a
    # worker whose last_update exceeds `timeout` with no exemption for
    # workers still booting, so a wait sitting at/near 60s races the arbiter's
    # kill signal. 10s x 3 attempts keeps the worst case around 30s.
    with engine.connect() as connection:
        acquired = None
        for _ in range(3):
            acquired = connection.exec_driver_sql(
                "SELECT GET_LOCK('wdis_schema_migration', 10)"
            ).scalar()
            if acquired == 1:
                break
            # acquired is 0 (timed out) or None (error): not acquired, retry.
        if acquired != 1:
            raise RuntimeError("timed out waiting for the schema migration lock")
        try:
            upgrade(directory=MIGRATIONS_DIR)
        finally:
            try:
                # Best-effort release: if upgrade() failed because the
                # connection died, RELEASE_LOCK would itself raise here and
                # replace the original exception/traceback. The lock is
                # released automatically by MariaDB when the connection
                # drops, so it's safe to swallow this failure.
                connection.exec_driver_sql("SELECT RELEASE_LOCK('wdis_schema_migration')")
            except Exception:
                pass


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db, directory=MIGRATIONS_DIR)
    app.register_blueprint(api)

    if _run_db_upgrade_enabled():
        with app.app_context():
            _upgrade_database()

    return app
