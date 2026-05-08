from .user_functions import _current_user, login_required, main
from flask import render_template, request, flash, abort, redirect, url_for
from . import db
from .models import Resource



@main.route("/resources")
@login_required
def resources():
    user = _current_user()

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
        narcotics_resources=narcotics_resources,
        user=user
    )




@main.route("/add-resource", methods=["POST"])
@login_required
def add_resource():
    user = _current_user()

    if not user:
        flash("User not found", "error")
        return redirect(url_for("main.login"))

    if user.role != "admin":
        abort(403)

    else:
        # data collected from form
        name = request.form.get("name", "").strip()
        url = request.form.get("url", "").strip()

        is_alcohol = "is_alcohol" in request.form
        is_narcotics = "is_narcotics" in request.form
        is_nicotine = "is_nicotine" in request.form

        # if fields not filled
        if not name or not url :
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("main.resources"))

        # using models.py class
        resource = Resource(
            name=name,
            url=url,
            is_alcohol=is_alcohol,
            is_narcotics=is_narcotics,
            is_nicotine=is_nicotine,
        )

        db.session.add(resource)
        db.session.commit()

        flash("Resource added successfully.", "success")
        return redirect(url_for("main.resources"))