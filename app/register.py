from .user_functions import main
from flask import  flash, redirect, url_for, request, session, render_template
from . import db
from .models import User
from datetime import datetime



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

        # create verified user
        user = User(
            username=pending["username"],
            email=pending["email"],
            password_hash=pending["password_hash"],
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
