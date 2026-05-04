import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    # Database (store in instance/app.db by default)
    DB_PATH = os.environ.get("DB_PATH", os.path.join(basedir, "instance", "app.db"))
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session cookie security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False  # set True in production with HTTPS

    # Crypto secrets
    PASSWORD_PEPPER = os.environ.get("PASSWORD_PEPPER", "dev-pepper-change-me")

    # Email config
    RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
    EMAIL_FROM = os.environ.get(
        "EMAIL_FROM",
        "48 Hours Forward <onboarding@resend.dev>"
    )

    # can create own Resend account
    # and add own API key for live email testing.

    # Fernet key (must be base64 urlsafe 32-byte key)
    BIO_ENCRYPTION_KEY = os.environ.get(
        "BIO_ENCRYPTION_KEY",
        "dOFoB-xRbITmNdBjxXTgCcQdpK65q_owWlLVSL8oeio=")

    DEBUG = True
    TESTING = False

    EMAIL_USER = os.environ.get("EMAIL_USER")
    EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")