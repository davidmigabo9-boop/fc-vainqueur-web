import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file, jsonify
from flask_login import login_required, current_user
from models.budget import Budget
from models.user import Utilisateur
from models.audit import AuditLog
from permissions import CRITICAL_ACTIONS
from extensions import db
from routes import role_required

budget_bp = Blueprint("budget", __name__, url_prefix="/budget")


@budget_bp.route("/")
@login_required
@role_required("budget_voir")
def index():
    operations = Budget.query.order_by(Budget.date_operation.desc()).all()
    recettes = Budget.total_recettes()
    depenses = Budget.total_depenses()
    solde = recettes - depenses
    now = datetime.now()
    recettes_mois = Budget.recettes_mois(now.month, now.year)
    depenses_mois = Budget.depenses_mois(now.month, now.year)
    return render_template("budget/index.html", operations=operations, recettes=recettes,
                           depenses=depenses, solde=solde, recettes_mois=recettes_mois,
                           depenses_mois=depenses_mois, page="budget")


@budget_bp.route("/ajouter", methods=["GET", "POST"])
@login_required
@role_required("budget_ajouter")
def ajouter():
    type_op = request.args.get("type", "recette")
    if request.method == "POST":
        motif = request.form.get("motif", "").strip()
        montant_str = request.form.get("montant", "0").strip()
        responsable = request.form.get("responsable", "").strip()
        date_op = request.form.get("date_operation", "").strip()
        try:
            montant = float(montant_str)
        except ValueError:
            flash("Montant invalide.", "warning")
            return render_template("budget/form.html", type_op=type_op, data={}, page="budget")
        if not motif or not date_op:
            flash("Motif et Date sont obligatoires.", "warning")
            return render_template("budget/form.html", type_op=type_op, data={}, page="budget")
        b = Budget(type_operation=type_op, motif=motif, montant=montant,
                   responsable=responsable, date_operation=date_op)
        db.session.add(b)
        db.session.commit()
        AuditLog.log(current_user.id, current_user.username, current_user.role,
                     f"Ajout {type_op}", f"Operation {type_op} : {motif} - {montant} FC")
        flash(f"{'Recette' if type_op == 'recette' else 'Depense'} ajoutee avec succes.", "success")
        return redirect(url_for("budget.index"))
    return render_template("budget/form.html", type_op=type_op, data={}, page="budget")


@budget_bp.route("/<int:budget_id>/modifier", methods=["GET", "POST"])
@login_required
@role_required("budget_ajouter")
def modifier(budget_id):
    b = Budget.query.get_or_404(budget_id)
    if request.method == "POST":
        motif = request.form.get("motif", "").strip()
        montant_str = request.form.get("montant", "0").strip()
        responsable = request.form.get("responsable", "").strip()
        date_op = request.form.get("date_operation", "").strip()
        try:
            montant = float(montant_str)
        except ValueError:
            flash("Montant invalide.", "warning")
            return render_template("budget/form.html", type_op=b.type_operation, data=b.__dict__, budget=b, page="budget")
        if not motif or not date_op:
            flash("Motif et Date sont obligatoires.", "warning")
            return render_template("budget/form.html", type_op=b.type_operation, data=b.__dict__, budget=b, page="budget")
        b.motif = motif
        b.montant = montant
        b.responsable = responsable
        b.date_operation = date_op
        db.session.commit()
        AuditLog.log(current_user.id, current_user.username, current_user.role,
                     f"Modification {b.type_operation}", f"Operation modifiee : {motif} - {montant} FC")
        flash("Operation modifiee avec succes.", "success")
        return redirect(url_for("budget.index"))
    return render_template("budget/form.html", type_op=b.type_operation, data=b.__dict__, budget=b, page="budget")


@budget_bp.route("/<int:budget_id>/supprimer", methods=["POST"])
@login_required
@role_required("budget_supprimer")
def supprimer(budget_id):
    b = Budget.query.get_or_404(budget_id)
    if current_user.is_super_admin():
        admin_pwd = request.form.get("admin_password", "")
        admin = Utilisateur.authenticate("admin", admin_pwd)
        if not admin or not admin.is_super_admin():
            flash("Mot de passe du Super Administrateur incorrect.", "danger")
            return redirect(url_for("budget.index"))
    motif = b.motif
    db.session.delete(b)
    db.session.commit()
    AuditLog.log(current_user.id, current_user.username, current_user.role,
                 CRITICAL_ACTIONS["supprimer_budget"], f"Operation supprimee : {motif} (ID: {budget_id})")
    flash("Operation supprimee avec succes.", "success")
    return redirect(url_for("budget.index"))


@budget_bp.route("/export/pdf")
@login_required
@role_required("budget_exporter")
def export_pdf():
    from exports.exporter import Exporter
    recettes = Budget.query.filter_by(type_operation="recette").order_by(Budget.date_operation.desc()).all()
    depenses = Budget.query.filter_by(type_operation="depense").order_by(Budget.date_operation.desc()).all()
    solde = Budget.solde()
    filepath = Exporter.export_budget_pdf_web(recettes, depenses, solde, current_app.config["EXPORTS_FOLDER"])
    return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))


@budget_bp.route("/export/excel")
@login_required
@role_required("budget_exporter")
def export_excel():
    from exports.exporter import Exporter
    recettes = Budget.query.filter_by(type_operation="recette").order_by(Budget.date_operation.desc()).all()
    depenses = Budget.query.filter_by(type_operation="depense").order_by(Budget.date_operation.desc()).all()
    filepath = Exporter.export_budget_excel_web(recettes, depenses, current_app.config["EXPORTS_FOLDER"])
    return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))


@budget_bp.route("/chart-data")
@login_required
def chart_data():
    data = Budget.get_par_mois()
    mois_map = {}
    for row in data:
        m = row.mois
        if m not in mois_map:
            mois_map[m] = {"recette": 0, "depense": 0}
        mois_map[m][row.type_operation] = row.total
    sorted_months = sorted(mois_map.keys())
    return jsonify({
        "labels": sorted_months,
        "recettes": [mois_map[m]["recette"] for m in sorted_months],
        "depenses": [mois_map[m]["depense"] for m in sorted_months],
    })
