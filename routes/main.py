from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models.joueur import Joueur, Contribution
from models.budget import Budget
from models.equipement import Equipement
from models.audit import AuditLog
from datetime import datetime
from routes import role_required

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def index():
    if current_user.has_perm("dashboard_voir"):
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("joueurs.index"))


@main_bp.route("/dashboard")
@login_required
@role_required("dashboard_voir")
def dashboard():
    now = datetime.now()
    mois = now.month
    annee = now.year

    stats = {
        "total_joueurs": Joueur.total_count(),
        "solde": Budget.solde(),
        "total_equipements": Equipement.total_quantite(),
        "total_contributions": Contribution.total_general(),
        "depenses_mois": Budget.depenses_mois(mois, annee),
        "recettes_mois": Budget.recettes_mois(mois, annee),
    }

    recent_logs = AuditLog.get_recent(5)
    return render_template("dashboard.html", stats=stats, recent_logs=recent_logs, page="dashboard")
