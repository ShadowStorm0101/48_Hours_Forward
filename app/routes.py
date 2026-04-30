import logging
import random
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
from sqlalchemy.orm import joinedload
from sqlalchemy import func

from . import db
from .models import User, Post
from .utils.validators import validate_email, validate_password, validate_bio, validate_username
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


def _current_user():
    uid = session.get("user_id")
    if not uid:
        return None

    user = db.session.get(User, uid)
    if not user:
        session.clear()

    return user

@main.route("/")
def home():
    return redirect(url_for("main.dashboard")) if session.get("user_id") else render_template("index.html")

@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            username = validate_username(request.form.get("public_username", ""))
            email = validate_email(request.form.get("email", ""))
            password = validate_password(request.form.get("password", ""), username=email)
            bio = validate_bio(request.form.get("bio", ""))
        except ValueError as e:
            flash(str(e), "error")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("Email already exists", "error")
            return redirect(url_for("main.login"))

        pepper = current_app.config["PASSWORD_PEPPER"]
        pw_hash = hash_password(password, pepper)

        code = str(random.randint(100000, 999999))

        user = User(
            username=username,
            email=email,
            password=pw_hash,
            bio=encrypt_bio(bio, current_app.config["BIO_ENCRYPTION_KEY"]) if bio else None,
            verification_code=code,
            verification_expiry=datetime.utcnow() + timedelta(minutes=5),
            is_verified=False
        )

        db.session.add(user)
        db.session.commit()

        # Store email in session
        session["verify_email"] = email

        send_verification_email(email, code)

        flash("Verification code sent!", "success")
        return redirect(url_for("main.verify"))

    return render_template("register.html")

@main.route("/verify", methods=["GET", "POST"])
def verify():
    email = session.get("verify_email")

    if not email:
        flash("Session expired. Register again.", "error")
        return redirect(url_for("main.register"))

    user = User.query.filter_by(email=email).first()

    if not user:
        flash("User not found", "error")
        return redirect(url_for("main.register"))

    if request.method == "POST":
        code = request.form.get("code")

        if datetime.utcnow() > user.verification_expiry:
            flash("Code expired", "error")
            return redirect(url_for("main.register"))

        if user.verification_code != code:
            flash("Invalid code", "error")
            return render_template("verify.html")

        user.is_verified = True
        user.verification_code = None
        user.verification_expiry = None

        db.session.commit()

        session.pop("verify_email", None)
        session["onboarding_user"] = user.id

        flash("Email verified", "success")
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

        user.alcohol = "alcohol" in addictions
        user.smoking = "smoking" in addictions
        user.narcotics = "narcotics" in addictions

        db.session.commit()

        session.pop("onboarding_user", None)

        flash("Profile setup complete!", "success")
        return redirect(url_for("main.login"))

    return render_template("onboarding.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and verify_password(password, user.password, current_app.config["PASSWORD_PEPPER"]):
            if not user.is_verified:
                session["verify_email"] = email
                flash("Verify your email first", "error")
                return redirect(url_for("main.verify"))

            session["user_id"] = user.id
            return redirect(url_for("main.dashboard"))

        flash("Invalid login", "error")

    return render_template("login.html")

@main.route("/dashboard")
@login_required
def dashboard():
    user = _current_user()
    if not user:
        session.clear()
        flash("Session expired. Please log in again.", "error")
        return redirect(url_for("main.login"))

    posts = (
        Post.query.options(joinedload(Post.author))
        .order_by(Post.created_at.desc())
        .limit(25)
        .all()
    )

    stats = None

    if user.role == "moderator":
        users = User.query.all()

        total_users = len(users)

        male = female = other = 0
        alcohol = smoking = narcotics = 0

        age_groups = {
            "under_18": 0,
            "18_25": 0,
            "26_40": 0,
            "40_plus": 0
        }

        for u in users:
            if u.gender == "male":
                male += 1
            elif u.gender == "female":
                female += 1
            elif u.gender == "other":
                other += 1

            if u.alcohol:
                alcohol += 1
            if u.smoking:
                smoking += 1
            if u.narcotics:
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
            "total_users": total_users,
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
        posts=posts,
        role=user.role,
        stats=stats
    )

@main.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=_current_user())

@main.route("/update-habits", methods=["POST"])
@login_required
def update_habits():
    user = _current_user()
    habit = request.form.get("habit")

    if habit == "alcohol":
        user.alcohol = not user.alcohol
    elif habit == "smoking":
        user.smoking = not user.smoking
    elif habit == "narcotics":
        user.narcotics = not user.narcotics

    db.session.commit()
    return redirect(url_for("main.profile"))

@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))