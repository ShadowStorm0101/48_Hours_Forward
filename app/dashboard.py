from datetime import datetime, timedelta
from .user_functions import _current_user, login_required, main
from flask import  flash, redirect, url_for, request
from . import db




# calculate distance to next milestone
def distance_milestone(delta):
    milestones = [1, 3, 7, 14, 30, 50, 100, 365, 1000]  # can be changed to further promote users sobriety

    for milestone in milestones:
        if delta.days < milestone:
            remaining = timedelta(days=milestone) - delta  # calc distance to milestone

            # format into hours and days
            total_hours = int(remaining.total_seconds() // 3600)
            total_days = remaining.days

            # if less than 72 hours show hours left, else show days
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

    # set user streak to be now
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

    flash(f"You have not failed {user.username}, now is a great time to go again", "success")
    return redirect(url_for("main.dashboard"))




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