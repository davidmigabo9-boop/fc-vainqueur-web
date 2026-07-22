from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user


def role_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if not current_user.has_perm(permission):
                flash("Vous n'avez pas les droits pour acceder a cette page.", "danger")
                if current_user.has_perm("dashboard_voir"):
                    return redirect(url_for("main.dashboard"))
                return redirect(url_for("joueurs.joueurs_list"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
