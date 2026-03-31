import logging
from datetime import datetime
from functools import wraps

from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
from sqlalchemy.orm import joinedload

from . import db
from .models import User, Post
from .utils.validators import validate_email, validate_password, validate_bio, validate_username
from .utils.sanitize import sanitize_html
from .utils.encryption import hash_password, verify_password, encrypt_bio

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
    return User.query.get(uid)

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
        raw_public_username = request.form.get("public_username", "")
        raw_email = request.form.get("email", "")
        raw_password = request.form.get("password", "")
        raw_bio = request.form.get("bio", "")

        ip = request.remote_addr or "unknown"
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        try:
            public_username = validate_username(raw_public_username)
            email = validate_email(raw_email)
            password = validate_password(raw_password, username=email)
            bio = validate_bio(raw_bio)
        except ValueError as e:
            flash(str(e), "error")
            security_logger.warning("REGISTER FAILED at %s ip=%s email=%r reason=%s", ts, ip, raw_email, str(e))
            return render_template("register.html")

        # uniqueness checks
        if User.query.filter_by(email=email).first():
            flash("Email already registered. Please log in.", "error")
            return redirect(url_for("main.login"))

        if User.query.filter_by(username=public_username).first():
            flash("That username is taken. Choose another.", "error")
            return render_template("register.html")

        safe_bio = sanitize_html(bio) if bio else ""
        encrypted_bio = encrypt_bio(safe_bio, current_app.config["BIO_ENCRYPTION_KEY"]) if safe_bio else None

        pepper = current_app.config["PASSWORD_PEPPER"]
        pw_hash = hash_password(password, pepper)

        user = User(username=public_username, email=email, password=pw_hash, role="user", bio=encrypted_bio)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful. Please log in.", "success")
        security_logger.info("REGISTER SUCCESS at %s ip=%s user_id=%s username=%r", ts, ip, user.id, user.username)
        return redirect(url_for("main.login"))

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

        if user and verify_password(raw_password.strip(), user.password, current_app.config["PASSWORD_PEPPER"]):
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

    # Optional: load posts (safe default)
    posts = (
        Post.query.options(joinedload(Post.author))
        .order_by(Post.created_at.desc())
        .limit(25)
        .all()
    )

    # Your dashboard.html currently only uses role, but keeping posts ready is useful later.
    return render_template("dashboard.html", role=user.role, posts=posts, user=user)

@main.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("main.login"))

@main.route("/journal")
@login_required
def journal():
    return render_template("journal.html")

@main.route("/resources")
@login_required
def resources():
    return render_template("resources.html")

@main.route("/map")
@login_required
def map():
    return render_template("map.html",
                           maps_api_key=current_app.config["MAPS_API_KEY"])

@main.route("/profile")
@login_required
def profile():
    return render_template("profile.html")

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
        if not verify_password(raw_current_password, user.password, pepper):
            flash("Current password is incorrect.", "error")
            return render_template("change_password.html")

        # Prevent reusing same password
        if verify_password(new_password, user.password, pepper):
            flash("New password must be different from your current password.", "error")
            return render_template("change_password.html")

        # Save new hash
        user.password = hash_password(new_password, pepper)
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
