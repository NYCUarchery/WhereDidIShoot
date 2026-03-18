from datetime import datetime, timezone

from flask import Blueprint, jsonify
from sqlalchemy import text

from .extensions import db


api = Blueprint("api", __name__, url_prefix="/api")


@api.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        db.session.rollback()
        return (
            jsonify(
                {
                    "status": "degraded",
                    "service": "backend",
                    "database": "unavailable",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            503,
        )

    return jsonify(
        {
            "status": "ok",
            "service": "backend",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
