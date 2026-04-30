from __future__ import annotations
from typing import List, Optional

from . import db
from sqlalchemy import Integer, String, ForeignKey, Enum, Text, DateTime, Boolean, true
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

    bio: Mapped[Optional[str]] = mapped_column(String(1200), nullable=True)

    alcohol: Mapped[bool] = mapped_column(Boolean, default=False)
    smoking: Mapped[bool] = mapped_column(Boolean, default=False)
    narcotics: Mapped[bool] = mapped_column(Boolean, default=False)

    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    verification_code: Mapped[Optional[str]] = mapped_column(String(6), nullable=True)
    verification_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    posts: Mapped[List["Post"]] = relationship(
        "Post",
        back_populates="author",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, username={self.username!r}, email={self.email!r}, role={self.role!r})"


class Post(db.Model):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    author: Mapped["User"] = relationship("User", back_populates="posts")


def seed_data():
    from flask import current_app
    from .utils.encryption import hash_password

    pepper = current_app.config["PASSWORD_PEPPER"]

    if User.query.count() == 0:
        admin = User(
            username="admin",
            email="admin@example.com",
            password=hash_password("Admin123!AAA", pepper),
            role="admin",
            is_verified=True
        )

        moderator = User(
            username="moderator",
            email="moderator@example.com",
            password=hash_password("Moderator123!AAA", pepper),
            role="moderator",
            is_verified=True
        )

        user1 = User(
            username="user1",
            email="user1@example.com",
            password=hash_password("User123!AAAA1", pepper),
            role="user",
            is_verified=True
        )

        db.session.add_all([admin, moderator, user1])
        db.session.commit()