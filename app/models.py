
from __future__ import annotations

from email.policy import default
from typing import List, Optional

from . import db
from sqlalchemy import Integer, String, ForeignKey, Enum, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum("user", "moderator", "admin", name="role_enum"),
        nullable=False,
        default="user",
    )
    alcohol_streak_start: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    narcotics_streak_start: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    nicotine_streak_start: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    # addiction_type: Mapped[str] = mapped_column(String(16), nullable=False) # We seem to use booleans, can revisit -zak


    def __repr__(self) -> str:
        return f"User(id={self.id!r}, username={self.username!r}, email={self.email!r}, role={self.role!r})"


def seed_data():
    """Populate sample users and posts (called from reset_db.py / run.py)."""
    from flask import current_app
    from .utils.encryption import hash_password

    pepper = current_app.config["PASSWORD_PEPPER"]

    # up until last session commit
    # if User.query.count() == 0:
    admin = User(
        username="admin",
        email="admin@example.com",
        password=hash_password("Admin123!AAA", pepper),
        role="admin",
        alcohol_streak_start=datetime.utcnow(),
        narcotics_streak_start = datetime.utcnow(),
        nicotine_streak_start = datetime.utcnow()
    )
    moderator = User(
        username="mod1",
        email="mod1@example.com",
        password=hash_password("Mod123!AAAA1", pepper),
        role="moderator",
        alcohol_streak_start=datetime.utcnow(),
        narcotics_streak_start=datetime.utcnow(),
        nicotine_streak_start=datetime.utcnow()
    )
    user1 = User(
        username="user1",
        email="user1@example.com",
        password=hash_password("User123!AAAA1", pepper),
        role="user",
        alcohol_streak_start=datetime.utcnow(),
        narcotics_streak_start=datetime.utcnow(),
        nicotine_streak_start=datetime.utcnow()
    )
    user2 = User(
        username="user2",
        email="user2@example.com",
        password=hash_password("User456!AAAA1", pepper),
        role="user",
        alcohol_streak_start=datetime.utcnow(),
        narcotics_streak_start=datetime.utcnow(),
        nicotine_streak_start=datetime.utcnow()
    )

    db.session.add_all([admin, moderator, user1, user2])
    db.session.commit()
