import os
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from models.user import Utilisateur
from models.audit import AuditLog
from permissions import get_role_label
from extensions import db
from werkzeug.security import check_password_hash

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
                return redirect(url_for("auth.selfie"))
            flash("Identifiant ou mot de passe incorrect.", "danger")
        except Exception as e:
            flash(f"Erreur de connexion: {str(e)}", "danger")
    return render_template("login.html")


@auth_bp.route("/selfie", methods=["GET", "POST"])
@login_required
def selfie():
    if request.method == "POST":
        import uuid
        from flask import current_app
        file = request.files.get("selfie")
        selfie_fn = ""
        if file and file.filename:
            ext = file.filename.rsplit(".", 1)[-1].lower()
            if ext in {"png", "jpg", "jpeg", "gif", "webp"}:
                filename = f"selfie_{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"
                selfie_dir = os.path.join(current_app.root_path, "static", "uploads", "selfies")
                os.makedirs(selfie_dir, exist_ok=True)
                file.save(os.path.join(selfie_dir, filename))
                selfie_fn = filename
        from models.login_attempt import LoginAttempt
        attempt = LoginAttempt(
            user_id=current_user.id,
            username=current_user.username,
            selfie_filename=selfie_fn,
            ip_address=request.remote_addr or "",
            user_agent=str(request.user_agent)[:300],
            statut="en_attente",
            vue_par_admin=0,
        )
        db.session.add(attempt)
        db.session.commit()
        logout_user()
        flash("Votre selfie est en attente de verification par l'administrateur.", "info")
        return redirect(url_for("auth.waiting", attempt_id=attempt.id))
    return render_template("selfie.html")


@auth_bp.route("/waiting/<int:attempt_id>")
def waiting(attempt_id):
    return render_template("waiting.html", attempt_id=attempt_id)


@auth_bp.route("/check-status/<int:attempt_id>")
def check_status(attempt_id):
    from models.login_attempt import LoginAttempt
    attempt = LoginAttempt.query.get(attempt_id)
    if not attempt:
        return {"status": "introuvable"}
    if attempt.statut == "autorise":
        user = Utilisateur.query.get(attempt.user_id)
        if user:
            login_user(user)
            try:
                AuditLog.log(user.id, user.username, user.role,
                             "Connexion autorisee", "Selfie verifie par l'admin")
            except Exception:
                pass
            if user.has_perm("dashboard_voir"):
                return {"status": "autorise", "redirect": "/dashboard"}
            return {"status": "autorise", "redirect": "/joueurs"}
    return {"status": attempt.statut}


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
