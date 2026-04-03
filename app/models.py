
from __future__ import annotations
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

    # encrypted bio (nullable)
    bio: Mapped[Optional[str]] = mapped_column(String(1200), nullable=True)


    alcohol: Mapped[bool] = mapped_column(default=False)
    smoking: Mapped[bool] = mapped_column(default=False)
    narcotics: Mapped[bool] = mapped_column(default=False)

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

    def __repr__(self) -> str:
        return f"Post(id={self.id!r}, title={self.title!r}, author_id={self.author_id!r})"


def seed_data():
    """Populate sample users and posts (called from reset_db.py / run.py)."""
    from flask import current_app
    from .utils.encryption import hash_password

    pepper = current_app.config["PASSWORD_PEPPER"]

    if User.query.count() == 0:
        admin = User(
            username="admin",
            email="admin@example.com",
            password=hash_password("Admin123!AAA", pepper),
            role="admin",
            bio=None,
        )
        moderator = User(
            username="mod1",
            email="mod1@example.com",
            password=hash_password("Mod123!AAAA1", pepper),
            role="moderator",
            bio=None,
        )
        user1 = User(
            username="user1",
            email="user1@example.com",
            password=hash_password("User123!AAAA1", pepper),
            role="user",
            bio=None,
        )
        user2 = User(
            username="user2",
            email="user2@example.com",
            password=hash_password("User456!AAAA1", pepper),
            role="user",
            bio=None,
        )

        db.session.add_all([admin, moderator, user1, user2])
        db.session.commit()

    if Post.query.count() == 0:
        users = User.query.order_by(User.id).all()
        if len(users) >= 4:
            post1 = Post(title="Welcome Post", content="This is the first post.", author_id=users[0].id)
            post2 = Post(title="Moderator Update", content="Moderator insights here.", author_id=users[1].id)
            post3 = Post(title="User Thoughts", content="User1 shares ideas.", author_id=users[2].id)
            post4 = Post(title="Another User Post", content="User2 contributes.", author_id=users[3].id)

            db.session.add_all([post1, post2, post3, post4])
            db.session.commit()
