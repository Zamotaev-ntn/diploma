from functools import wraps
from flask import current_app, abort, flash, redirect, url_for
from flask_login import current_user, login_required


def role_required(required_role):
    def decorator(func):
        @wraps(func)
        @login_required
        def wrapper(*args, **kwargs):
            if current_user.role != required_role:
                flash("Доступ запрещён", "danger")
                return redirect(url_for("index"))
            return func(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(func):
    @wraps(func)
    @role_required(2)  # ROLE_ADMIN = 2
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper