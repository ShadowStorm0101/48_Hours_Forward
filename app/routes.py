import logging
import random
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

from . import db

from .models import User, LocationService, Resource, JournalEntry
from .utils.email_notifications import send_checkin_reminder_email

from .models import User

from .utils.validators import validate_email, validate_password, validate_bio, validate_username
from .utils.sanitize import sanitize_html
from .utils.encryption import hash_password, verify_password, encrypt_bio
from .utils.email import send_verification_email

main = Blueprint("main", __name__)

security_logger = logging.getLogger("security")

def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("main.login"))
        return view_func(*args, **kwargs)
    return wrapped_view

def _current_user() -> User | None:
    uid = session.get("user_id")
    if not uid:
        return None

    user = db.session.get(User, uid)
    if not user:
        session.clear()

    return user



def distance_milestone(delta):
    milestones = [1, 3, 7, 14, 30, 50, 100, 365, 1000]

    for milestone in milestones:
        if delta.days < milestone:
            remaining = timedelta(days=milestone) - delta

            total_hours = int(remaining.total_seconds() // 3600)
            total_days = remaining.days

            if total_hours <= 72:
                return f"{total_hours} hours until your {milestone} day milestone!"

            return f"{total_days} days until your {milestone} day milestone!"

    return "All milestones achieved!"


@main.route("/reset-habit/<habit>", methods=["POST"])
@login_required
def reset_habit(habit):
    user = _current_user()

    if not user:
        flash("Please log in first.", "error")
        return redirect(url_for("main.login"))

    if habit == "alcohol":
        user.alcohol_streak_start = datetime.utcnow()
    elif habit == "nicotine":
        user.nicotine_streak_start = datetime.utcnow()
    elif habit == "narcotics":
        user.narcotics_streak_start = datetime.utcnow()
    else:
        # this should never logically occur - z
        flash("Invalid habit.", "error")
        return redirect(url_for("main.dashboard"))

    db.session.commit()

    flash(f"{habit.capitalize()} streak reset.", "success")
    return redirect(url_for("main.dashboard"))



@main.route("/")
def home():
    # If already logged in, skip landing page
    if session.get("user_id"):
        return redirect(url_for("main.dashboard"))
    else:
        return render_template("index.html")

@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        raw_username = request.form.get("public_username", "")
        raw_email = request.form.get("email", "")
        raw_password = request.form.get("password", "")

        try:
            username = validate_username(raw_username)
            email = validate_email(raw_email)
            password = validate_password(raw_password, username=email)
        except ValueError as e:
            flash(str(e), "error")
            return render_template("register.html")

        # uniqueness checks BEFORE proceeding
        if User.query.filter_by(email=email).first():
            flash("Email already exists", "error")
            return redirect(url_for("main.login"))

        if User.query.filter_by(username=username).first():
            flash("Username taken", "error")
            return render_template("register.html")

        # generate verification code
        code = str(random.randint(100000, 999999))

        # store TEMP data in session (NOT DB)
        session["pending_user"] = {
            "username": username,
            "email": email,
            "password": password  # plain for now, hash later
        }
        session["verification_code"] = code

        send_verification_email(email, code)

        flash("Verification code sent!", "success")
        return redirect(url_for("main.verify"))

    return render_template("register.html")

@main.route("/verify", methods=["GET", "POST"])
def verify():
    pending = session.get("pending_user")
    code_expected = session.get("verification_code")

    if not pending or not code_expected:
        flash("Session expired. Register again.", "error")
        return redirect(url_for("main.register"))

    if request.method == "POST":
        code_input = request.form.get("code")

        if code_input != code_expected:
            flash("Invalid code", "error")
            return render_template("verify.html")

        # ✅ NOW create user
        pepper = current_app.config["PASSWORD_PEPPER"]
        password_hash = hash_password(pending["password"], pepper)

        user = User(
            username=pending["username"],
            email=pending["email"],
            password_hash=password_hash,
            is_verified=True
        )

        db.session.add(user)
        db.session.commit()

        # cleanup session
        session.pop("pending_user", None)
        session.pop("verification_code", None)

        session["onboarding_user"] = user.id

        flash("Email verified!", "success")
        return redirect(url_for("main.onboarding"))

    return render_template("verify.html")


@main.route("/onboarding", methods=["GET", "POST"])
def onboarding():
    user_id= session.get("onboarding_user")

    if not user_id:
        flash("Session expired. please register again.", "error")
        return redirect(url_for("main.register"))

    user = db.session.get(User,user_id)

    if not user:
        flash("User not found", "error")
        return redirect(url_for("main.register"))

    if request.method == "POST":
        gender = request.form.get("gender")
        age = request.form.get("age")
        addictions = request.form.getlist("addictions")

        user.gender = gender
        user.age = int(age) if age else None

        if request.form.get("alcohol"):
            user.alcohol_streak_start = datetime.utcnow()
        if request.form.get("nicotine"):
            user.nicotine_streak_start = datetime.utcnow()
        if request.form.get("narcotics"):
            user.narcotics_streak_start = datetime.utcnow()

        db.session.commit()

        session.pop("onboarding_user", None)

        flash("Profile setup complete!", "success")
        return redirect(url_for("main.login"))

    return render_template("onboarding.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        raw_email = request.form.get("email", "")
        raw_password = request.form.get("password", "")

        ip = request.remote_addr or "unknown"
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        if not raw_email or not raw_password:
            flash("Please enter both email and password.", "error")
            return render_template("login.html")

        user = User.query.filter_by(email=raw_email.strip()).first()

        if user and verify_password(raw_password.strip(), user.password_hash, current_app.config["PASSWORD_PEPPER"]):
            user.last_login_at = datetime.utcnow()
            db.session.commit()

            session["user_id"] = user.id
            session["role"] = user.role
            flash(f"Logged in as {user.username}", "success")

            current_app.logger.info(
                "LOGIN SUCCESS at %s ip=%s user_id=%s username=%r role=%s",
                ts, ip, user.id, user.username, user.role
            )
            return redirect(url_for("main.dashboard"))

        flash("Invalid email or password.", "error")
        current_app.logger.warning("LOGIN FAILED at %s ip=%s email=%r", ts, ip, raw_email)
        return render_template("login.html")

    return render_template("login.html")

@main.route("/dashboard")
@login_required
def dashboard():
    user = _current_user()
    if not user:
        flash("Please log in first.", "error")
        return redirect(url_for("main.login"))

    # ALCOHOL
    if user.alcohol_streak_start is not None:
        alcohol_delta = datetime.utcnow() - user.alcohol_streak_start
        alcohol_milestone_message = distance_milestone(alcohol_delta)
    else:
        current_alcohol_streak = None
        alcohol_milestone_message = None

    # NICOTINE
    if user.nicotine_streak_start is not None:
        nicotine_delta = datetime.utcnow() - user.nicotine_streak_start
        nicotine_milestone_message = distance_milestone(nicotine_delta)
    else:
        current_nicotine_streak = None
        nicotine_milestone_message = None

    # NARCOTICS
    if user.narcotics_streak_start is not None:
        narcotics_delta = datetime.utcnow() - user.narcotics_streak_start
        narcotics_milestone_message = distance_milestone(narcotics_delta)
    else:
        current_narcotics_streak = None
        narcotics_milestone_message = None

    edit = request.args.get("edit")

    return render_template(
        "dashboard.html",
        user=user,
        alcohol_milestone_message=alcohol_milestone_message,
        nicotine_milestone_message=nicotine_milestone_message,
        narcotics_milestone_message=narcotics_milestone_message,
        edit=edit
    )



@main.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("main.login"))

@main.route("/journal")
@login_required
def journal():
    user = _current_user()
    if not user:
        flash("Please log in first.", "error")
        return redirect(url_for("main.login"))

    selected_entry_id = request.args.get("entry_id", type=int)

    entries = (
        JournalEntry.query
        .filter_by(user_id=user.id)
        .order_by(JournalEntry.updated_at.desc())
        .all())

    favourites = [entry for entry in entries if entry.is_favourite]
    recent = [entry for entry in entries if not entry.is_favourite]

    active_entry = None
    if entries:
        if selected_entry_id is not None:
            active_entry = next((entry for entry in entries if entry.id == selected_entry_id), None)
        if active_entry is None:
            active_entry = entries[0]

    return render_template("journal.html",
        favourites=favourites,
        recent=recent,
        active_entry=active_entry)

@main.route("/journal/new", methods=["POST"])
@login_required
def create_journal_entry():
    user = _current_user()
    if not user:
        flash("Please log in first.", "error")
        return redirect(url_for("main.login"))

    entry = JournalEntry(
        title="New Entry",
        content="",
        user_id=user.id,
        is_favourite=False)
    db.session.add(entry)
    db.session.commit()

    return redirect(url_for("main.journal", entry_id=entry.id))

@main.route("/journal/<int:entry_id>/save", methods=["POST"])
@login_required
def save_journal_entry(entry_id):
    user = _current_user()
    if not user:
        flash("Please log in first.", "error")
        return redirect(url_for("main.login"))

    entry = JournalEntry.query.filter_by(id=entry_id, user_id=user.id).first_or_404()

    raw_title = request.form.get("title", "").strip()
    raw_content = request.form.get("content", "").strip()

    entry.title = raw_title[:120] if raw_title else "Untitled"
    entry.content = sanitize_html(raw_content)

    db.session.commit()
    flash("Journal entry saved.", "success")
    return redirect(url_for("main.journal", entry_id=entry.id))


@main.route("/journal/<int:entry_id>/toggle-favourite", methods=["POST"])
@login_required
def toggle_journal_favourite(entry_id):
    user = _current_user()
    if not user:
        flash("Please log in first.", "error")
        return redirect(url_for("main.login"))

    entry = JournalEntry.query.filter_by(id=entry_id, user_id=user.id).first_or_404()
    entry.is_favourite = not entry.is_favourite
    db.session.commit()

    return redirect(url_for("main.journal", entry_id=entry.id))

@main.route("/journal/<int:entry_id>/delete", methods=["POST"])
@login_required
def delete_journal_entry(entry_id):
    user = _current_user()
    if not user:
        flash("Please log in first.", "error")
        return redirect(url_for("main.login"))

    entry = JournalEntry.query.filter_by(id=entry_id, user_id=user.id).first_or_404()

    db.session.delete(entry)
    db.session.commit()

    flash("Journal entry deleted.", "success")
    return redirect(url_for("main.journal"))

@main.route("/resources")
@login_required
def resources():

    alcohol_resources = Resource.query.filter_by(
        is_alcohol=True
    ).all()

    nicotine_resources = Resource.query.filter_by(
        is_nicotine=True
    ).all()

    narcotics_resources = Resource.query.filter_by(
        is_narcotics=True
    ).all()

    return render_template(
        "resources.html",
        alcohol_resources=alcohol_resources,
        nicotine_resources=nicotine_resources,
        narcotics_resources=narcotics_resources
    )

@main.route("/map")
@login_required
def map():
    user_lat = request.args.get("lat", type=float)
    user_lng = request.args.get("lng", type=float)
    if (user_lat == None or user_lng == None):
        user_lat = 54.9783
        user_lng = -1.6178

    user = _current_user()
    conditions = []

    if user.alcohol_streak_start is not None:
        conditions.append(LocationService.is_alcohol.is_(True))

    if user.nicotine_streak_start is not None:
        conditions.append(LocationService.is_nicotine.is_(True))

    if user.narcotics_streak_start is not None:
        conditions.append(LocationService.is_narcotics.is_(True))

    R = 6371 #Earths circumference km

    #Haversine formula for distance
    distance = (
            R * func.acos(
        func.cos(func.radians(user_lat)) *
        func.cos(func.radians(LocationService.lat)) *
        func.cos(func.radians(LocationService.lng) - func.radians(user_lng)) +
        func.sin(func.radians(user_lat)) *
        func.sin(func.radians(LocationService.lat))
    )
    ).label("distance")
    total_in_db = LocationService.query.count()
    current_app.logger.warning(f"🗺️ MAP DEBUG: Total location services in DB: {total_in_db}")
    query = db.session.query(LocationService, distance)

    if conditions:
        query = query.filter(or_(*conditions))

    services = (
        query
        .order_by(distance)
        .limit(50)
        .all()
    )

    DAY_MAP = {
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
        5: "Saturday",
        6: "Sunday",
    }

    places = [
        {
            "name": s.LocationService.name,
            "lat": s.LocationService.lat,
            "lng": s.LocationService.lng,
            "day": DAY_MAP[s.LocationService.day],
            "time": s.LocationService.time.strftime("%H:%M"),
            "is_alcohol": s.LocationService.is_alcohol,
            "is_narcotics": s.LocationService.is_narcotics,
            "is_nicotine": s.LocationService.is_nicotine,
            "distance_km": s.distance
        }
        for s in services
    ]

    return render_template("map.html",
                           maps_api_key=current_app.config["MAPS_API_KEY"],
                           places = places)

@main.route("/profile")
@login_required
def profile():
    user = _current_user()

    if not user:
        flash("User not found", "error")
        return redirect(url_for("main.login"))

    return render_template("profile.html", user=user)

@main.route("/update-habits", methods=["POST"])
@login_required
def update_habits():
    user = _current_user()

    if not user:
        flash("User not found", "error")
        return redirect(url_for("main.login"))

    selected = request.form.getlist("habits")
    print("selected habits:", selected)

    # Apply choices, Also need to call function to start addiction time
    if "alcohol" in selected:
        if user.alcohol_streak_start is None:
            user.alcohol_streak_start = datetime.utcnow()
    else:
        user.alcohol_streak_start = None

    if "nicotine" in selected:
        if user.nicotine_streak_start is None:
            user.nicotine_streak_start = datetime.utcnow()
    else:
        user.nicotine_streak_start = None

    if "narcotics" in selected:
        if user.narcotics_streak_start is None:
            user.narcotics_streak_start = datetime.utcnow()
    else:
        user.narcotics_streak_start = None

    db.session.commit()

    flash("Preferences updated!", "success")


    return redirect(url_for("main.profile"))

@main.route("/reset")
@login_required
def reset():
    user = _current_user()

    #### If in the dashboard the addiction selected = *addiction type then*
    # user.alcohol_streak_start_streak_start = datetime.utcnow()
    # user.nicotine_streak_start = datetime.utcnow()
    # user.narcotics_streak_start = datetime.utcnow()             # calls function to set datetime to now

    db.session.commit()             # commit to db
    return redirect(url_for("main.dashboard"))

@main.route("/send-reminders")
def send_reminders():
    now = datetime.utcnow()

    inactive_users = User.query.filter(
        User.last_login_at != None,
        User.last_login_at <= now - timedelta(days=1),
        User.reminder_email_enabled == True
    ).all()

    emails_sent = 0

    for user in inactive_users:
        if (
            user.last_reminder_sent_at is None
            or user.last_reminder_sent_at <= now - timedelta(days=1)
        ):
            email_sent = send_checkin_reminder_email(user)

            if email_sent:
                user.last_reminder_sent_at = now
                emails_sent += 1

    db.session.commit()

    return f"{emails_sent} reminder emails sent."

@main.route("/help")
@login_required
def help():
    return render_template("help.html")

def require_login():
    # Logged in if user_id exists
    if "user_id" not in session:
        return redirect(url_for("main.login"))
    return None





# SQL injection and invalid inputs. 
@main.route("/change-password", methods=["GET", "POST"])
def change_password():
    resp = require_login()
    if resp:
        flash("Please log in first.", "error")
        return resp

    user_id = session.get("user_id")
    role = session.get("role", "user")

    user = User.query.get(user_id)
    if not user:
        session.clear()
        flash("Session expired. Please log in again.", "error")
        return redirect(url_for("main.login"))

    if request.method == "POST":
        raw_current_password = request.form.get("current_password", "").strip()
        raw_new_password = request.form.get("new_password", "").strip()

        if not raw_current_password or not raw_new_password:
            flash("Please fill in both password fields.", "error")
            return render_template("change_password.html")

        try:
            # Validate new password strength (don’t validate current with strength rules)
            new_password = validate_password(raw_new_password, username=user.email)
        except ValueError as e:
            flash(str(e), "error")
            return render_template("change_password.html")

        pepper = current_app.config["PASSWORD_PEPPER"]

        # Verify current password against stored hash
        if not verify_password(raw_current_password, user.password_hash, pepper):
            flash("Current password is incorrect.", "error")
            return render_template("change_password.html")

        # Prevent reusing same password
        if verify_password(new_password, user.password_hash, pepper):
            flash("New password must be different from your current password.", "error")
            return render_template("change_password.html")

        # Save new hash
        user.password_hash = hash_password(new_password, pepper)
        db.session.commit()

        security_logger.info(
            "PASSWORD CHANGE SUCCESS user_id=%s username=%r ip=%s",
            user.id, user.username, request.remote_addr
        )

        # Keep session consistent (don’t clear it)
        session["user_id"] = user.id
        session["role"] = user.role

        flash("Password changed successfully.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("change_password.html")
