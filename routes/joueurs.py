import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models.joueur import Joueur, Contribution
from models.user import Utilisateur
from models.audit import AuditLog
from permissions import CRITICAL_ACTIONS
from extensions import db
from routes import role_required
from datetime import datetime

joueurs_bp = Blueprint("joueurs", __name__, url_prefix="/joueurs")


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]


def _save_photo(file, joueur_id=None):
    if file and file.filename and _allowed_file(file.filename):
        ext = file.filename.rsplit(".", 1)[1].lower()
        prefix = f"joueur_{joueur_id}_" if joueur_id else "joueur_"
        filename = f"{prefix}{uuid.uuid4().hex[:8]}.{ext}"
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        return filename
    return ""


@joueurs_bp.route("/")
@login_required
@role_required("joueurs_voir")
def index():
    if current_user.role == "lecteur":
        if current_user.joueur_id:
            return redirect(url_for("joueurs.fiche", joueur_id=current_user.joueur_id))
        return redirect(url_for("auth.mon_profil"))
    terme = request.args.get("q", "").strip()
    if terme:
        joueurs = Joueur.search(terme)
    else:
        joueurs = Joueur.active_joueurs()
    return render_template("joueurs/index.html", joueurs=joueurs, terme=terme, page="joueurs")


@joueurs_bp.route("/ajouter", methods=["GET", "POST"])
@login_required
@role_required("joueurs_ajouter")
def ajouter():
    if request.method == "POST":
        data = _extract_form_data(request)
        if not data["nom"] or not data["prenom"]:
            flash("Nom et Prenom sont obligatoires.", "warning")
            return render_template("joueurs/form.html", joueur=None, data=data, page="joueurs")
        photo_file = request.files.get("photo")
        joueur = Joueur(**data)
        db.session.add(joueur)
        db.session.flush()
        if photo_file and photo_file.filename:
            filename = _save_photo(photo_file, joueur.id)
            if filename:
                joueur.photo = filename
        db.session.commit()
        AuditLog.log(current_user.id, current_user.username, current_user.role,
                     "Ajout joueur", f"Joueur ajoute : {joueur.prenom} {joueur.nom}")
        flash("Joueur ajoute avec succes.", "success")
        return redirect(url_for("joueurs.index"))
    return render_template("joueurs/form.html", joueur=None, data={}, page="joueurs")


@joueurs_bp.route("/<int:joueur_id>")
@login_required
@role_required("joueurs_voir")
def fiche(joueur_id):
    if current_user.role == "lecteur" and current_user.joueur_id != joueur_id:
        flash("Vous ne pouvez voir que votre propre fiche.", "warning")
        if current_user.joueur_id:
            return redirect(url_for("joueurs.fiche", joueur_id=current_user.joueur_id))
        return redirect(url_for("joueurs.index"))
    joueur = Joueur.query.get_or_404(joueur_id)
    contributions = Contribution.query.filter_by(joueur_id=joueur_id).order_by(Contribution.date_contribution.desc()).all()
    total = joueur.total_contributions()
    from age_utils import format_age, categorie_automatique, potentiel_joueur
    age_exact = format_age(joueur.date_naissance)
    categorie = categorie_automatique(joueur.date_naissance)
    potentiel = potentiel_joueur(joueur.date_naissance)
    return render_template("joueurs/fiche.html", joueur=joueur, contributions=contributions,
                           total=total, page="joueurs", age_exact=age_exact,
                           categorie=categorie, potentiel=potentiel)


@joueurs_bp.route("/<int:joueur_id>/evolution")
@login_required
@role_required("joueurs_voir")
def evolution(joueur_id):
    if current_user.role == "lecteur" and current_user.joueur_id != joueur_id:
        flash("Vous ne pouvez voir que votre propre evolution.", "warning")
        if current_user.joueur_id:
            return redirect(url_for("joueurs.evolution", joueur_id=current_user.joueur_id))
        return redirect(url_for("joueurs.index"))
    joueur = Joueur.query.get_or_404(joueur_id)
    from age_utils import (format_age, categorie_automatique, anniversaire_info,
                           alerte_changement_categorie, potentiel_joueur,
                           recommandation_joueur, annees_au_club)
    age_exact = format_age(joueur.date_naissance)
    categorie = categorie_automatique(joueur.date_naissance)
    anniversaire = anniversaire_info(joueur.date_naissance)
    alerte_categorie = alerte_changement_categorie(joueur.date_naissance)
    potentiel = potentiel_joueur(joueur.date_naissance)
    recommandation = recommandation_joueur(joueur.date_naissance)
    annees_club = annees_au_club(joueur.date_inscription)
    return render_template("joueurs/evolution.html",
                           joueur=joueur, page="joueurs",
                           age_exact=age_exact, categorie=categorie,
                           anniversaire=anniversaire, alerte_categorie=alerte_categorie,
                           potentiel=potentiel, recommandation=recommandation,
                           annees_club=annees_club)


@joueurs_bp.route("/lier/<int:joueur_id>", methods=["POST"])
@login_required
def lier_compte(joueur_id):
    if current_user.role != "lecteur":
        flash("Seuls les lecteurs peuvent lier leur compte.", "warning")
        return redirect(url_for("joueurs.index"))
    joueur = Joueur.query.get_or_404(joueur_id)
    current_user.joueur_id = joueur_id
    db.session.commit()
    AuditLog.log(current_user.id, current_user.username, current_user.role,
                 "Lien compte-joueur", f"Compte lie au joueur : {joueur.prenom} {joueur.nom}")
    flash(f"Votre compte est lie a {joueur.prenom} {joueur.nom}.", "success")
    return redirect(url_for("joueurs.fiche", joueur_id=joueur_id))


@joueurs_bp.route("/<int:joueur_id>/modifier", methods=["GET", "POST"])
@login_required
@role_required("joueurs_modifier")
def modifier(joueur_id):
    joueur = Joueur.query.get_or_404(joueur_id)
    if request.method == "POST":
        data = _extract_form_data(request)
        if not data["nom"] or not data["prenom"]:
            flash("Nom et Prenom sont obligatoires.", "warning")
            return render_template("joueurs/form.html", joueur=joueur, data=data, page="joueurs")
        photo_file = request.files.get("photo")
        for key, value in data.items():
            setattr(joueur, key, value)
        if photo_file and photo_file.filename:
            filename = _save_photo(photo_file, joueur.id)
            if filename:
                joueur.photo = filename
        db.session.commit()
        AuditLog.log(current_user.id, current_user.username, current_user.role,
                     "Modification joueur", f"Joueur modifie : {joueur.prenom} {joueur.nom}")
        flash("Joueur modifie avec succes.", "success")
        return redirect(url_for("joueurs.fiche", joueur_id=joueur.id))
    return render_template("joueurs/form.html", joueur=joueur, data=joueur.__dict__, page="joueurs")


@joueurs_bp.route("/<int:joueur_id>/supprimer", methods=["POST"])
@login_required
@role_required("joueurs_supprimer")
def supprimer(joueur_id):
    joueur = Joueur.query.get_or_404(joueur_id)
    nom = f"{joueur.prenom} {joueur.nom}"
    if current_user.is_super_admin():
        admin_pwd = request.form.get("admin_password", "")
        admin = Utilisateur.authenticate("admin", admin_pwd)
        if not admin or not admin.is_super_admin():
            flash("Mot de passe du Super Administrateur incorrect.", "danger")
            return redirect(url_for("joueurs.fiche", joueur_id=joueur_id))
    db.session.delete(joueur)
    db.session.commit()
    AuditLog.log(current_user.id, current_user.username, current_user.role,
                 CRITICAL_ACTIONS["supprimer_joueur"], f"Joueur supprime : {nom} (ID: {joueur_id})")
    flash("Joueur supprime avec succes.", "success")
    return redirect(url_for("joueurs.index"))


@joueurs_bp.route("/<int:joueur_id>/contributions/ajouter", methods=["POST"])
@login_required
@role_required("contributions_ajouter")
def ajouter_contribution(joueur_id):
    joueur = Joueur.query.get_or_404(joueur_id)
    try:
        montant = float(request.form.get("montant", 0))
    except ValueError:
        flash("Montant invalide.", "warning")
        return redirect(url_for("joueurs.fiche", joueur_id=joueur_id))
    description = request.form.get("description", "").strip()
    date = request.form.get("date_contribution", "").strip()
    if not date:
        flash("La date est obligatoire.", "warning")
        return redirect(url_for("joueurs.fiche", joueur_id=joueur_id))
    c = Contribution(joueur_id=joueur_id, montant=montant, description=description, date_contribution=date)
    db.session.add(c)
    db.session.commit()
    AuditLog.log(current_user.id, current_user.username, current_user.role,
                 "Ajout contribution", f"Contribution {montant} FC pour {joueur.prenom} {joueur.nom}")
    flash("Contribution ajoute avec succes.", "success")
    return redirect(url_for("joueurs.fiche", joueur_id=joueur_id))


@joueurs_bp.route("/export/pdf")
@login_required
@role_required("joueurs_exporter")
def export_pdf():
    from exports.exporter import Exporter
    joueurs = Joueur.active_joueurs()
    filepath = Exporter.export_joueurs_pdf_web(joueurs, current_app.config["EXPORTS_FOLDER"])
    return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))


@joueurs_bp.route("/export/excel")
@login_required
@role_required("joueurs_exporter")
def export_excel():
    from exports.exporter import Exporter
    joueurs = Joueur.active_joueurs()
    filepath = Exporter.export_joueurs_excel_web(joueurs, current_app.config["EXPORTS_FOLDER"])
    return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))


def _extract_form_data(req):
    return {
        "nom": req.form.get("nom", "").strip(),
        "postnom": req.form.get("postnom", "").strip(),
        "prenom": req.form.get("prenom", "").strip(),
        "numero": int(req.form.get("numero", 0) or 0),
        "poste": req.form.get("poste", ""),
        "date_naissance": req.form.get("date_naissance", "").strip(),
        "telephone": req.form.get("telephone", "").strip(),
        "date_inscription": req.form.get("date_inscription", "").strip(),
    }
