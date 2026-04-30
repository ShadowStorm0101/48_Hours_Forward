import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

from config import Config

db = SQLAlchemy()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    print(app.config["SQLALCHEMY_DATABASE_URI"])
    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Init extensions
    db.init_app(app)
    csrf.init_app(app)

    # Logging
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)

    # Import models so SQLAlchemy sees them
    from . import models

    # Blueprints
    from .routes import main
    app.register_blueprint(main)

    return app
