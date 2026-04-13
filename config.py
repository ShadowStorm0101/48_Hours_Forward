import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    DB_PATH = os.environ.get("DB_PATH", os.path.join(basedir, "instance", "app.db"))
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False

    PASSWORD_PEPPER = os.environ.get("PASSWORD_PEPPER", "dev-pepper-change-me")

    BIO_ENCRYPTION_KEY = os.environ.get(
        "BIO_ENCRYPTION_KEY",
        "dOFoB-xRbITmNdBjxXTgCcQdpK65q_owWlLVSL8oeio="
    )

    DEBUG = True
    TESTING = False

    EMAIL_USER = os.environ.get("EMAIL_USER")
    EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")