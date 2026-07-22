import os
import shutil
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models.user import Utilisateur
from models.audit import AuditLog
from permissions import CRITICAL_ACTIONS, ROLES, ROLE_LABELS, get_role_key
from extensions import db
from routes import role_required

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/")
@login_required
@role_required("parametres_voir")
def index():
    users = Utilisateur.query.order_by(Utilisateur.nom_complet).all()
    backups = _list_backups()
    audit_logs = AuditLog.get_recent(50)
    return render_template("settings/index.html", users=users, backups=backups,
                           audit_logs=audit_logs, roles=ROLES, role_labels=ROLE_LABELS,
                           page="settings")


@settings_bp.route("/ajouter-utilisateur", methods=["POST"])
@login_required
@role_required("utilisateurs_voir")
def ajouter_utilisateur():
    nom = request.form.get("nom", "").strip()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    role_label = request.form.get("role", "Lecteur")
    if not nom or not username or not password:
        flash("Tous les champs sont obligatoires.", "warning")
        return redirect(url_for("settings.index"))
    if current_user.is_super_admin():
        admin_pwd = request.form.get("admin_password", "")
        admin = Utilisateur.authenticate("admin", admin_pwd)
        if not admin or not admin.is_super_admin():
            flash("Mot de passe du Super Administrateur incorrect.", "danger")
            return redirect(url_for("settings.index"))
    role_key = get_role_key(role_label)
    user = Utilisateur(nom_complet=nom, username=username, role=role_key)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    AuditLog.log(current_user.id, current_user.username, current_user.role,
                 CRITICAL_ACTIONS["gerer_utilisateurs"],
                 f"Utilisateur ajoute : {username} (role: {role_label})")
    flash(f"Utilisateur '{username}' ajoute avec succes.", "success")
    return redirect(url_for("settings.index"))


@settings_bp.route("/supprimer-utilisateur/<int:user_id>", methods=["POST"])
@login_required
@role_required("utilisateurs_supprimer")
def supprimer_utilisateur(user_id):
    user = Utilisateur.query.get_or_404(user_id)
    if user.username == "admin":
        flash("Impossible de supprimer l'administrateur principal.", "danger")
        return redirect(url_for("settings.index"))
    if current_user.is_super_admin():
        admin_pwd = request.form.get("admin_password", "")
        admin = Utilisateur.authenticate("admin", admin_pwd)
        if not admin or not admin.is_super_admin():
            flash("Mot de passe du Super Administrateur incorrect.", "danger")
            return redirect(url_for("settings.index"))
    username = user.username
    db.session.delete(user)
    db.session.commit()
    AuditLog.log(current_user.id, current_user.username, current_user.role,
                 CRITICAL_ACTIONS["supprimer_utilisateur"],
                 f"Utilisateur supprime : {username} (ID: {user_id})")
    flash("Utilisateur supprime.", "success")
    return redirect(url_for("settings.index"))


@settings_bp.route("/sauvegarder", methods=["POST"])
@login_required
@role_required("sauvegarde_creer")
def sauvegarder():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_uri = current_app.config["SQLALCHEMY_DATABASE_URI"]
    if db_uri.startswith("sqlite:///"):
        db_path = db_uri[len("sqlite:///"):]
    else:
        db_path = db_uri
    backup_path = os.path.join(current_app.config["BACKUPS_FOLDER"], f"backup_{timestamp}.db")
    shutil.copy2(db_path, backup_path)
    AuditLog.log(current_user.id, current_user.username, current_user.role,
                 "Sauvegarde", f"Sauvegarde creee : backup_{timestamp}.db")
    flash("Sauvegarde creee avec succes.", "success")
    return redirect(url_for("settings.index"))


@settings_bp.route("/restaurer/<filename>", methods=["POST"])
@login_required
@role_required("sauvegarde_restaurer")
def restaurer(filename):
    if current_user.is_super_admin():
        admin_pwd = request.form.get("admin_password", "")
        admin = Utilisateur.authenticate("admin", admin_pwd)
        if not admin or not admin.is_super_admin():
            flash("Mot de passe du Super Administrateur incorrect.", "danger")
            return redirect(url_for("settings.index"))
    backup_path = os.path.join(current_app.config["BACKUPS_FOLDER"], filename)
    if not os.path.isfile(backup_path):
        flash("Sauvegarde introuvable.", "danger")
        return redirect(url_for("settings.index"))
    db_uri = current_app.config["SQLALCHEMY_DATABASE_URI"]
    if db_uri.startswith("sqlite:///"):
        db_path = db_uri[len("sqlite:///"):]
    else:
        db_path = db_uri
    shutil.copy2(backup_path, db_path)
    AuditLog.log(current_user.id, current_user.username, current_user.role,
                 CRITICAL_ACTIONS["restaurer_sauvegarde"],
                 f"Base restauree depuis : {filename}")
    flash("Base de donnees restauree. Reconnectez-vous.", "success")
    return redirect(url_for("auth.logout"))


@settings_bp.route("/reset-password/<int:user_id>", methods=["POST"])
@login_required
@role_required("parametres_modifier")
def reset_password(user_id):
    user = Utilisateur.query.get_or_404(user_id)
    new_password = request.form.get("new_password", "").strip()
    if not new_password:
        flash("Le mot de passe ne peut pas etre vide.", "warning")
        return redirect(url_for("settings.index"))
    user.set_password(new_password)
    db.session.commit()
    AuditLog.log(current_user.id, current_user.username, current_user.role,
                 "Modification mot de passe", f"Mot de passe de {user.username} modifie")
    flash(f"Mot de passe de {user.username} mis a jour.", "success")
    return redirect(url_for("settings.index"))


def _list_backups():
    folder = current_app.config["BACKUPS_FOLDER"]
    try:
        files = sorted([f for f in os.listdir(folder) if f.endswith(".db")], reverse=True)
    except FileNotFoundError:
        files = []
    backups = []
    for f in files:
        path = os.path.join(folder, f)
        size = os.path.getsize(path)
        backups.append({"name": f, "size": f"{size / 1024:.1f} KB"})
    return backups


@settings_bp.route("/programmes")
@login_required
@role_required("parametres_modifier")
def programmes():
    from models.programme import Programme
    progs = Programme.query.order_by(Programme.date_evenement.desc()).all()
    return render_template("settings/programmes.html", programmes=progs, page="settings")


@settings_bp.route("/programmes/ajouter", methods=["POST"])
@login_required
@role_required("parametres_modifier")
def ajouter_programme():
    from models.programme import Programme
    titre = request.form.get("titre", "").strip()
    lieu = request.form.get("lieu", "").strip()
    date_evt = request.form.get("date_evenement", "").strip()
    heure = request.form.get("heure", "").strip()
    description = request.form.get("description", "").strip()
    if not titre or not lieu or not date_evt or not heure:
        flash("Tous les champs sont obligatoires.", "warning")
        return redirect(url_for("settings.programmes"))
    p = Programme(titre=titre, lieu=lieu, date_evenement=date_evt, heure=heure, description=description)
    db.session.add(p)
    db.session.commit()
    AuditLog.log(current_user.id, current_user.username, current_user.role,
                 "Ajout programme", f"Programme ajoute : {titre} le {date_evt}")
    flash("Programme ajoute avec succes.", "success")
    return redirect(url_for("settings.programmes"))


@settings_bp.route("/programmes/supprimer/<int:prog_id>", methods=["POST"])
@login_required
@role_required("parametres_modifier")
def supprimer_programme(prog_id):
    from models.programme import Programme
    p = Programme.query.get_or_404(prog_id)
    titre = p.titre
    db.session.delete(p)
    db.session.commit()
    AuditLog.log(current_user.id, current_user.username, current_user.role,
                 "Suppression programme", f"Programme supprime : {titre}")
    flash("Programme supprime.", "success")
    return redirect(url_for("settings.programmes"))


@settings_bp.route("/photos")
@login_required
@role_required("parametres_modifier")
def photos():
    from models.photo import Photo
    all_photos = Photo.get_all()
    return render_template("settings/photos.html", photos=all_photos, page="settings")


@settings_bp.route("/photos/ajouter", methods=["POST"])
@login_required
@role_required("parametres_modifier")
def ajouter_photo():
    from models.photo import Photo
    from werkzeug.utils import secure_filename
    import uuid
    file = request.files.get("photo")
    titre = request.form.get("titre", "").strip()
    if not file or not file.filename:
        flash("Veuillez selectionner une photo.", "warning")
        return redirect(url_for("settings.photos"))
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in {"png", "jpg", "jpeg", "gif", "bmp", "webp"}:
        flash("Format non supporte.", "warning")
        return redirect(url_for("settings.photos"))
    filename = f"pub_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)
    photo = Photo(filename=filename, titre=titre)
    db.session.add(photo)
    db.session.commit()
    AuditLog.log(current_user.id, current_user.username, current_user.role,
                 "Ajout photo", f"Photo publique ajoutee : {filename}")
    flash("Photo ajoutee avec succes.", "success")
    return redirect(url_for("settings.photos"))


@settings_bp.route("/photos/supprimer/<int:photo_id>", methods=["POST"])
@login_required
@role_required("parametres_modifier")
def supprimer_photo(photo_id):
    from models.photo import Photo
    p = Photo.query.get_or_404(photo_id)
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], p.filename)
    if os.path.isfile(filepath):
        os.remove(filepath)
    db.session.delete(p)
    db.session.commit()
    AuditLog.log(current_user.id, current_user.username, current_user.role,
                 "Suppression photo", f"Photo supprimee : {p.filename}")
    flash("Photo supprimee.", "success")
    return redirect(url_for("settings.photos"))
