import random
from datetime import datetime, timedelta

from flask import render_template, request, flash, redirect, url_for, session, current_app

from . import db
from .models import User, JournalEntry
from .utils.email_notifications import send_checkin_reminder_email
from .utils.validators import validate_email, validate_password, validate_username
from .utils.encryption import hash_password, verify_password
from .utils.email import send_verification_email
from .dashboard import distance_milestone
from .user_functions import _current_user, login_required, main, security_logger

from . import journal
from . import register
from . import map
from . import resources


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
        confirm_password = request.form.get("confirm_password", "")

        # confirm passwords match
        if raw_password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        try:
            username = validate_username(raw_username)
            email = validate_email(raw_email)
            password = validate_password(raw_password, username=email)
        except ValueError as e:
            flash(str(e), "error")
            return render_template("register.html")

        # uniqueness checks
        if User.query.filter_by(email=email).first():
            flash("Email already exists", "error")
            return redirect(url_for("main.login"))

        if User.query.filter_by(username=username).first():
            flash("Username taken", "error")
            return render_template("register.html")

        # HASH PASSWORD IMMEDIATELY
        pepper = current_app.config["PASSWORD_PEPPER"]
        password_hash = hash_password(password, pepper)

        # generate verification code
        code = str(random.randint(100000, 999999))

        # store ONLY SAFE DATA in session
        session["pending_user"] = {
            "username": username,
            "email": email,
            "password_hash": password_hash
        }

        session["verification_code"] = code

        send_verification_email(email, code)

        flash("Verification code sent!", "success")
        return redirect(url_for("main.verify"))

    return render_template("register.html")



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
        alcohol_milestone_message = None

    # NICOTINE
    if user.nicotine_streak_start is not None:
        nicotine_delta = datetime.utcnow() - user.nicotine_streak_start
        nicotine_milestone_message = distance_milestone(nicotine_delta)
    else:
        nicotine_milestone_message = None

    # NARCOTICS
    if user.narcotics_streak_start is not None:
        narcotics_delta = datetime.utcnow() - user.narcotics_streak_start
        narcotics_milestone_message = distance_milestone(narcotics_delta)
    else:
        narcotics_milestone_message = None

    stats = None

    if user.role == "moderator":
        users = User.query.all()

        male = female = other = 0
        alcohol = smoking = narcotics = 0

        age_groups = {
            "under_18": 0,
            "18_25": 0,
            "26_40": 0,
            "40_plus": 0
        }

        # iterate through users, add to counter
        for u in users:
            if u.gender == "male":
                male += 1
            elif u.gender == "female":
                female += 1
            elif u.gender == "other":
                other += 1

            # increasing counts
            if u.alcohol_streak_start is not None:
                alcohol += 1

            if u.nicotine_streak_start is not None:
                smoking += 1

            if u.narcotics_streak_start is not None:
                narcotics += 1

            if u.age is not None:
                if u.age < 18:
                    age_groups["under_18"] += 1
                elif 18 <= u.age <= 25:
                    age_groups["18_25"] += 1
                elif 26 <= u.age <= 40:
                    age_groups["26_40"] += 1
                else:
                    age_groups["40_plus"] += 1

        stats = {
            "gender": {
                "male": male,
                "female": female,
                "other": other
            },
            "addictions": {
                "alcohol": alcohol,
                "smoking": smoking,
                "narcotics": narcotics
            },
            "age_groups": age_groups
        }

    return render_template(
        "dashboard.html",
        user=user,
        role=user.role,
        stats=stats,
        alcohol_milestone_message=alcohol_milestone_message,
        nicotine_milestone_message=nicotine_milestone_message,
        narcotics_milestone_message=narcotics_milestone_message
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


@main.route("/profile")
@login_required
def profile():
    user = _current_user()

    if not user:
        flash("User not found", "error")
        return redirect(url_for("main.login"))

    return render_template("profile.html", user=user)


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
