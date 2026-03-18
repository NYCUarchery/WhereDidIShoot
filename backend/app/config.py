import os
from urllib.parse import quote_plus


def build_database_uri() -> str:
    user = quote_plus(os.getenv("DB_USER", "app"))
    password = quote_plus(os.getenv("DB_PASSWORD", "app_password"))
    host = os.getenv("DB_HOST", "db")
    port = os.getenv("DB_PORT", "3306")
    name = os.getenv("DB_NAME", "app")

    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change-me")
    SQLALCHEMY_DATABASE_URI = build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
