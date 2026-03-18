from flask import Flask

from .config import Config
from .extensions import db
from .routes import api


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    app.register_blueprint(api)

    return app
