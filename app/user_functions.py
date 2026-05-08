from functools import wraps
from flask import  flash, redirect, url_for, session, Blueprint
from . import db
from .models import User
import logging

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