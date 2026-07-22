import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from flask_login import login_required, current_user
from models.equipement import Equipement
from models.user import Utilisateur
from models.audit import AuditLog
from permissions import CRITICAL_ACTIONS
from extensions import db
from routes import role_required

equipements_bp = Blueprint("equipements", __name__, url_prefix="/equipements")


@equipements_bp.route("/")
@login_required
@role_required("equipements_voir")
def index():
    terme = request.args.get("q", "").strip()
    if terme:
        equipements = Equipement.search(terme)
    else:
        equipements = Equipement.query.order_by(Equipement.nom).all()
    return render_template("equipements/index.html", equipements=equipements, terme=terme, page="equipements")


@equipements_bp.route("/ajouter", methods=["GET", "POST"])
@login_required
@role_required("equipements_ajouter")
def ajouter():
    if request.method == "POST":
        data = _extract_form_data(request)
        if not data["nom"]:
            flash("Le nom est obligatoire.", "warning")
            return render_template("equipements/form.html", equipement=None, data=data, page="equipements")
        eq = Equipement(**data)
        db.session.add(eq)
        db.session.commit()
        AuditLog.log(current_user.id, current_user.username, current_user.role,
                     "Ajout equipement", f"Equipement ajoute : {eq.nom}")
        flash("Equipement ajoute avec succes.", "success")
        return redirect(url_for("equipements.index"))
    return render_template("equipements/form.html", equipement=None, data={}, page="equipements")


@equipements_bp.route("/<int:eq_id>/modifier", methods=["GET", "POST"])
@login_required
@role_required("equipements_modifier")
def modifier(eq_id):
    eq = Equipement.query.get_or_404(eq_id)
    if request.method == "POST":
        data = _extract_form_data(request)
        if not data["nom"]:
            flash("Le nom est obligatoire.", "warning")
            return render_template("equipements/form.html", equipement=eq, data=data, page="equipements")
        for key, value in data.items():
            setattr(eq, key, value)
        db.session.commit()
        AuditLog.log(current_user.id, current_user.username, current_user.role,
                     "Modification equipement", f"Equipement modifie : {eq.nom}")
        flash("Equipement modifie avec succes.", "success")
        return redirect(url_for("equipements.index"))
    return render_template("equipements/form.html", equipement=eq, data=eq.__dict__, page="equipements")


@equipements_bp.route("/<int:eq_id>/supprimer", methods=["POST"])
@login_required
@role_required("equipements_supprimer")
def supprimer(eq_id):
    eq = Equipement.query.get_or_404(eq_id)
    if current_user.is_super_admin():
        admin_pwd = request.form.get("admin_password", "")
        admin = Utilisateur.authenticate("admin", admin_pwd)
        if not admin or not admin.is_super_admin():
            flash("Mot de passe du Super Administrateur incorrect.", "danger")
            return redirect(url_for("equipements.index"))
    nom = eq.nom
    db.session.delete(eq)
    db.session.commit()
    AuditLog.log(current_user.id, current_user.username, current_user.role,
                 CRITICAL_ACTIONS["supprimer_equipement"], f"Equipement supprime : {nom} (ID: {eq_id})")
    flash("Equipement supprime avec succes.", "success")
    return redirect(url_for("equipements.index"))


@equipements_bp.route("/export/pdf")
@login_required
@role_required("equipements_exporter")
def export_pdf():
    from exports.exporter import Exporter
    equipements = Equipement.query.order_by(Equipement.nom).all()
    filepath = Exporter.export_equipements_pdf_web(equipements, current_app.config["EXPORTS_FOLDER"])
    return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))


@equipements_bp.route("/export/excel")
@login_required
@role_required("equipements_exporter")
def export_excel():
    from exports.exporter import Exporter
    equipements = Equipement.query.order_by(Equipement.nom).all()
    filepath = Exporter.export_equipements_excel_web(equipements, current_app.config["EXPORTS_FOLDER"])
    return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))


def _extract_form_data(req):
    data = {
        "nom": req.form.get("nom", "").strip(),
        "categorie": req.form.get("categorie", "").strip(),
        "description": req.form.get("description", "").strip(),
        "etat": req.form.get("etat", "Neuf"),
        "fournisseur": req.form.get("fournisseur", "").strip(),
        "observations": req.form.get("observations", "").strip(),
        "date_achat": req.form.get("date_achat", "").strip(),
    }
    try:
        data["quantite"] = int(req.form.get("quantite", 1) or 1)
    except ValueError:
        data["quantite"] = 1
    try:
        data["prix"] = float(req.form.get("prix", 0) or 0)
    except ValueError:
        data["prix"] = 0
    return data
