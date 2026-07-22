from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from models.user import Utilisateur
from models.audit import AuditLog
from permissions import get_role_label

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if not username or not password:
            flash("Veuillez remplir tous les champs.", "warning")
            return render_template("login.html")
        user = Utilisateur.authenticate(username, password)
        if user:
            login_user(user)
            AuditLog.log(
                user.id, user.username, user.role,
                "Connexion",
                f"Connexion reussie - Role: {get_role_label(user.role)}",
            )
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.dashboard"))
        flash("Identifiant ou mot de passe incorrect.", "danger")
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    AuditLog.log(
        current_user.id, current_user.username, current_user.role,
        "Deconnexion",
        "Deconnexion",
    )
    logout_user()
    return redirect(url_for("auth.login"))
