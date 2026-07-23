from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.feuille_match import FeuilleDeMatch
from models.joueur import Joueur
from routes import role_required
from datetime import datetime

feuilles_bp = Blueprint("feuilles", __name__)


@feuilles_bp.route("/feuilles")
@login_required
@role_required("feuilles_voir")
def index():
    feuilles = FeuilleDeMatch.get_all()
    return render_template("feuilles/index.html", feuilles=feuilles, page="feuilles")


@feuilles_bp.route("/feuilles/ajouter", methods=["GET", "POST"])
@login_required
@role_required("feuilles_ajouter")
def ajouter():
    joueurs = Joueur.active_joueurs()
    if request.method == "POST":
        f = FeuilleDeMatch(
            date_match=request.form.get("date_match", ""),
            heure_match=request.form.get("heure_match", ""),
            lieu=request.form.get("lieu", ""),
            adversaire=request.form.get("adversaire", ""),
            score_fcv=int(request.form.get("score_fcv") or 0),
            score_adv=int(request.form.get("score_adv") or 0),
            titulaires_json=json.dumps(request.form.getlist("titulaires")),
            remplacants_json=json.dumps(request.form.getlist("remplacants")),
            tactique=request.form.get("tactique", ""),
            blessures=request.form.get("blessures", ""),
            suspensions=request.form.get("suspensions", ""),
            equipements=request.form.get("equipements", ""),
            notes=request.form.get("notes", ""),
            statut=request.form.get("statut", "planifie"),
            cree_par=current_user.id,
        )
        import json
        f.titulaires_json = json.dumps(request.form.getlist("titulaires"))
        f.remplacants_json = json.dumps(request.form.getlist("remplacants"))
        from extensions import db
        db.session.add(f)
        db.session.commit()
        flash("Feuille de match creee avec succes!", "success")
        return redirect(url_for("feuilles.detail", feuille_id=f.id))
    return render_template("feuilles/form.html", feuille=None, joueurs=joueurs, page="feuilles")


@feuilles_bp.route("/feuilles/<int:feuille_id>")
@login_required
@role_required("feuilles_voir")
def detail(feuille_id):
    feuille = FeuilleDeMatch.query.get_or_404(feuille_id)
    joueurs_map = {str(j.id): j for j in Joueur.active_joueurs()}
    titulaires = [joueurs_map[jid] for jid in feuille.get_titulaires() if jid in joueurs_map]
    remplacants = [joueurs_map[jid] for jid in feuille.get_remplacants() if jid in joueurs_map]
    return render_template("feuilles/detail.html", feuille=feuille,
                           titulaires=titulaires, remplacants=remplacants, page="feuilles")


@feuilles_bp.route("/feuilles/<int:feuille_id>/modifier", methods=["GET", "POST"])
@login_required
@role_required("feuilles_modifier")
def modifier(feuille_id):
    import json
    feuille = FeuilleDeMatch.query.get_or_404(feuille_id)
    joueurs = Joueur.active_joueurs()
    if request.method == "POST":
        feuille.date_match = request.form.get("date_match", feuille.date_match)
        feuille.heure_match = request.form.get("heure_match", feuille.heure_match)
        feuille.lieu = request.form.get("lieu", feuille.lieu)
        feuille.adversaire = request.form.get("adversaire", feuille.adversaire)
        feuille.score_fcv = int(request.form.get("score_fcv") or 0)
        feuille.score_adv = int(request.form.get("score_adv") or 0)
        feuille.titulaires_json = json.dumps(request.form.getlist("titulaires"))
        feuille.remplacants_json = json.dumps(request.form.getlist("remplacants"))
        feuille.tactique = request.form.get("tactique", "")
        feuille.blessures = request.form.get("blessures", "")
        feuille.suspensions = request.form.get("suspensions", "")
        feuille.equipements = request.form.get("equipements", "")
        feuille.notes = request.form.get("notes", "")
        feuille.statut = request.form.get("statut", feuille.statut)
        from extensions import db
        db.session.commit()
        flash("Feuille de match modifiee!", "success")
        return redirect(url_for("feuilles.detail", feuille_id=feuille.id))
    return render_template("feuilles/form.html", feuille=feuille, joueurs=joueurs, page="feuilles")


@feuilles_bp.route("/feuilles/<int:feuille_id>/supprimer", methods=["POST"])
@login_required
@role_required("feuilles_supprimer")
def supprimer(feuille_id):
    from extensions import db
    feuille = FeuilleDeMatch.query.get_or_404(feuille_id)
    db.session.delete(feuille)
    db.session.commit()
    flash("Feuille de match supprimee.", "danger")
    return redirect(url_for("feuilles.index"))
