from .user_functions import _current_user, login_required, main
from flask import render_template, request, current_app, flash, abort, redirect, url_for
from .models import User, LocationService
from sqlalchemy import func, or_
from . import db
import datetime


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
                           places = places,
                           user=user)


@main.route("/add-location", methods=["POST"])
@login_required
def add_location():
    user = _current_user()

    if not user:
        flash("User not found", "error")
        return redirect(url_for("main.login"))

    if user.role != "admin":
        abort(403)

    else:
        # data collected from form
        name = request.form.get("name", "").strip()
        lat = float(request.form.get("lat"))
        lng = float(request.form.get("lng"))
        day = int(request.form.get("day"))
        time_raw = request.form.get("time", "")

        is_alcohol = "is_alcohol" in request.form
        is_nicotine = "is_nicotine" in request.form
        is_narcotics = "is_narcotics" in request.form

        # if fields not filled
        if not name or lat is None or lng is None or day is None or not time_raw:
            flash("Please fill in all required location fields.", "error")
            return redirect(url_for("main.map"))

        # using models.py class
        location = LocationService(
            name=name,
            lat=lat,
            lng=lng,
            day=day,
            time=datetime.strptime(time_raw, "%H:%M").time(),
            is_alcohol=is_alcohol,
            is_nicotine=is_nicotine,
            is_narcotics=is_narcotics
        )

        db.session.add(location)
        db.session.commit()


        flash("Location added successfully.", "success")
        return redirect(url_for("main.map", lat=lat, lng=lng, zoom=16))
