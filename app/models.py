from __future__ import annotations
import csv
import os
from flask import current_app
from . import db
from sqlalchemy import Integer, String, Float, Enum, DateTime, Boolean, Time
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, time


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum("user", "moderator", "admin", name="role_enum"),
        nullable=False,
        default="user",
    )
    alcohol_streak_start: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    narcotics_streak_start: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    nicotine_streak_start: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    # addiction_type: Mapped[str] = mapped_column(String(16), nullable=False) # We seem to use booleans, can revisit -zak
    last_login_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_reminder_sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    reminder_email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, username={self.username!r}, email={self.email!r}, role={self.role!r})"


class LocationService(db.Model):
    __tablename__ = "location_services"

    id:Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    lat: Mapped[float] = mapped_column(Float, index=True, nullable=False)
    lng: Mapped[float] = mapped_column(Float, index=True, nullable=False)

    day: Mapped[int] = mapped_column(Integer, index=True, nullable=False) #0=Mon, 1=Tue etc
    time: Mapped[time] = mapped_column(Time, index=True, nullable=False)

    is_alcohol: Mapped[bool] = mapped_column(Boolean, default=False)
    is_narcotics: Mapped[bool] = mapped_column(Boolean, default=False)
    is_nicotine: Mapped[bool] = mapped_column(Boolean, default=False)

class Resource(db.Model):
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    url: Mapped[str] = mapped_column(String(255), nullable=False)

    is_alcohol: Mapped[bool] = mapped_column(Boolean, default=False)
    is_nicotine: Mapped[bool] = mapped_column(Boolean, default=False)
    is_narcotics: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self):
        return f"Resource(id={self.id}, name={self.name})"

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
        password_hash=hash_password("Admin123!AAA", pepper),
        role="admin",
        alcohol_streak_start=None,
        narcotics_streak_start=None,
        nicotine_streak_start=None
    )
    moderator = User(
        username="mod1",
        email="mod1@example.com",
        password_hash=hash_password("Mod123!AAAA1", pepper),
        role="moderator",
        alcohol_streak_start=None,
        narcotics_streak_start=None,
        nicotine_streak_start=None
    )
    user1 = User(
        username="user1",
        email="user1@example.com",
        password_hash=hash_password("User123!AAAA1", pepper),
        role="user",
        alcohol_streak_start=None,
        narcotics_streak_start=None,
        nicotine_streak_start=None
    )
    user2 = User(
        username="user2",
        email="user2@example.com",
        password_hash=hash_password("User456!AAAA1", pepper),
        role="user",
        alcohol_streak_start=None,
        narcotics_streak_start=None,
        nicotine_streak_start=None
    )

    db.session.add_all([admin, moderator, user1, user2])
    db.session.commit()
    seed_resources()


def seed_location_services_from_csv():
    csv_path = os.path.join(current_app.root_path, "static", "database_data", "meetings-2025-05-19.csv")

    print(f"🔍 Looking for CSV at: {csv_path}")
    print(f"🔍 File exists: {os.path.exists(csv_path)}")

    with open(csv_path, 'r', encoding='utf-8-sig') as csv_file:
        reader = csv.DictReader(csv_file)

        print(f"🔍 CSV Headers found: {reader.fieldnames}")

        DAY_MAP = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6,
        }

        row_count = 0
        added_count = 0

        for row in reader:
            row_count += 1

            if not row.get("Name"):
                continue

            try:
                lat = float(row["Latitude"])
                lng = float(row["Longitude"])
                day = DAY_MAP[row["Day"]]
                parsed_time = datetime.strptime(row["Time"], "%H:%M").time()
                is_alcohol = row.get("IsAlcohol", "0").strip() == "1"
                is_narcotics = row.get("IsNarcotics", "0").strip() == "1"
                is_nicotine = row.get("IsNicotine", "0").strip() == "1"

                service = LocationService(
                    name=row["Name"].strip(),
                    lat=lat,
                    lng=lng,
                    day=day,
                    time=parsed_time,
                    is_alcohol=is_alcohol,
                    is_narcotics=is_narcotics,
                    is_nicotine=is_nicotine,
                )

                db.session.add(service)
                added_count += 1

            except ValueError as e:
                print(f"Skipping row {row_count} due to conversion error: {row.get('Name', 'Unknown')} ({e})")
                continue

        db.session.commit()

def seed_resources_from_csv():
    csv_path = os.path.join(
        current_app.root_path,
        "static",
        "database_data",
        "resources.csv"
    )



    with open(csv_path) as csv_file:
        reader = csv.DictReader(csv_file)

        for row in reader:
            if not row.get("Name"):
                continue

            resource = Resource(
                name=row["Name"].strip(),
                url=row["URL"].strip(),
                is_alcohol=row.get("IsAlcohol", "0").strip() == "1",
                is_nicotine=row.get("IsNicotine", "0").strip() == "1",
                is_narcotics=row.get("IsNarcotics", "0").strip() == "1"
            )

            db.session.add(resource)

        db.session.commit()

def seed_location_services():
    print(f"🔍 seed_location_services() called")
    if LocationService.query.count() == 0:
        print("🔍 Database has 0 location services, seeding now...")
        seed_location_services_from_csv()
    else:
        print(f"🔍 Database already has {LocationService.query.count()} location services, skipping seed")

def seed_resources():
    if Resource.query.count() == 0:
        seed_resources_from_csv()