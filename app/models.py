from __future__ import annotations

import csv
import os
from typing import List, Optional

from flask import current_app

from . import db
from sqlalchemy import Integer, String, Float, ForeignKey, Enum, Text, DateTime, Boolean
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

class LocationService(db.Model):
    __tablename__ = "location_services"

    id:Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    lat: Mapped[float] = mapped_column(Float, index=True, nullable=False)
    lng: Mapped[float] = mapped_column(Float, index=True, nullable=False)

    is_alcohol: Mapped[bool] = mapped_column(Boolean, default=False)
    is_narcotics: Mapped[bool] = mapped_column(Boolean, default=False)
    is_nicotine: Mapped[bool] = mapped_column(Boolean, default=False)

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

    if LocationService.query.count() == 0:
        seed_location_services_from_csv()


def seed_location_services_from_csv():
    csv_path = os.path.join(current_app.root_path,"static","database_data","location_services.csv")
    with open(csv_path) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            # Skip empty rows or rows without a name
            if not row.get("Name"):
                continue

            try:
                lat = float(row["Latitude"])
                lng = float(row["Longitude"])
                is_alcohol = row.get("IsAlcohol", "0").strip() == "1"
                is_narcotics = row.get("IsNarcotics", "0").strip() == "1"
                is_nicotine = row.get("IsNicotine", "0").strip() == "1"

            except ValueError as e:
                print(f"Skipping row due to conversion error: {row} ({e})")
                continue

            service = LocationService(
                name=row["Name"].strip(),
                lat=lat,
                lng=lng,
                is_alcohol=is_alcohol,
                is_narcotics=is_narcotics,
                is_nicotine=is_nicotine,
            )

            db.session.add(service)
        db.session.commit()
