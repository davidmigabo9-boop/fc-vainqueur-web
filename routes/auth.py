import os
from datetime import datetime
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
                if user.is_super_admin():
                    next_page = request.args.get("next")
                    if next_page:
                        return redirect(next_page)
                    if user.has_perm("dashboard_voir"):
                        return redirect(url_for("main.dashboard"))
                    return redirect(url_for("joueurs.index"))
                if user.role == "lecteur":
                    if user.joueur_id:
                        return redirect(url_for("joueurs.fiche", joueur_id=user.joueur_id))
                    return redirect(url_for("auth.mon_profil"))
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
            if user.role == "lecteur":
                if user.joueur_id:
                    return {"status": "autorise", "redirect": f"/joueurs/{user.joueur_id}"}
                return {"status": "autorise", "redirect": "/mon-profil"}
            if user.has_perm("dashboard_voir"):
                return {"status": "autorise", "redirect": "/dashboard"}
            return {"status": "autorise", "redirect": "/joueurs"}
    return {"status": attempt.statut}


@auth_bp.route("/mon-profil", methods=["GET", "POST"])
@login_required
def mon_profil():
    if current_user.role != "lecteur":
        if current_user.has_perm("dashboard_voir"):
            return redirect(url_for("main.dashboard"))
        return redirect(url_for("joueurs.index"))
    if current_user.joueur_id:
        return redirect(url_for("joueurs.fiche", joueur_id=current_user.joueur_id))
    if request.method == "POST":
        import uuid as uid
        from flask import current_app
        from models.joueur import Joueur
        nom = request.form.get("nom", "").strip()
        prenom = request.form.get("prenom", "").strip()
        if not nom or not prenom:
            flash("Nom et Prenom sont obligatoires.", "warning")
            return render_template("profil.html")
        joueur = Joueur(
            nom=nom,
            postnom=request.form.get("postnom", "").strip(),
            prenom=prenom,
            numero=int(request.form.get("numero", 0) or 0),
            poste=request.form.get("poste", ""),
            date_naissance=request.form.get("date_naissance", "").strip(),
            telephone=request.form.get("telephone", "").strip(),
            adresse=request.form.get("adresse", "").strip(),
            date_inscription=datetime.now().strftime("%Y-%m-%d"),
        )
        db.session.add(joueur)
        db.session.flush()
        photo_file = request.files.get("photo")
        if photo_file and photo_file.filename:
            ext = photo_file.filename.rsplit(".", 1)[-1].lower()
            if ext in {"png", "jpg", "jpeg", "gif", "bmp", "webp"}:
                filename = f"joueur_{joueur.id}_{uid.uuid4().hex[:8]}.{ext}"
                filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                photo_file.save(filepath)
                joueur.photo = filename
        current_user.joueur_id = joueur.id
        current_user.nom_complet = f"{prenom} {nom}"
        db.session.commit()
        AuditLog.log(current_user.id, current_user.username, current_user.role,
                     "Profil complete", f"Joueur cree : {prenom} {nom}")
        flash("Profil enregistre avec succes!", "success")
        return redirect(url_for("joueurs.fiche", joueur_id=joueur.id))
    return render_template("profil.html")


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
