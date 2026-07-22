from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from models.user import Utilisateur
from models.audit import AuditLog
from permissions import get_role_label
import traceback

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if not username or not password:
            flash("Veuillez remplir tous les champs.", "warning")
            return render_template("login.html")
        try:
            user = Utilisateur.authenticate(username, password)
            if user:
                login_user(user)
                try:
                    AuditLog.log(
                        user.id, user.username, user.role,
                        "Connexion",
                        f"Connexion reussie - Role: {get_role_label(user.role)}",
                    )
                except Exception:
                    pass
                next_page = request.args.get("next")
                if next_page:
                    return redirect(next_page)
                if user.has_perm("dashboard_voir"):
                    return redirect(url_for("main.dashboard"))
                return redirect(url_for("joueurs.index"))
            flash("Identifiant ou mot de passe incorrect.", "danger")
        except Exception as e:
            flash(f"Erreur de connexion: {str(e)}", "danger")
    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nom_complet = request.form.get("nom_complet", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if not nom_complet or not username or not password:
            flash("Veuillez remplir tous les champs.", "warning")
            return render_template("register.html")
        if Utilisateur.query.filter_by(username=username).first():
            flash("Ce nom d'utilisateur existe deja.", "danger")
            return render_template("register.html")
        user = Utilisateur(
            nom_complet=nom_complet,
            username=username,
            role="lecteur",
        )
        user.set_password(password)
        from extensions import db
        db.session.add(user)
        db.session.commit()
        AuditLog.log(
            user.id, user.username, user.role,
            "Inscription",
            f"Inscription automatique - Role: Lecteur",
        )
        flash("Compte cree! Connectez-vous.", "success")
        return redirect(url_for("auth.login"))
    return render_template("register.html")


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
