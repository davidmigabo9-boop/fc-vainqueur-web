from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models.login_attempt import LoginAttempt
from routes import role_required

security_bp = Blueprint("security", __name__, url_prefix="/security")


@security_bp.route("/")
@login_required
@role_required("parametres_voir")
def center():
    attempts = LoginAttempt.get_all()
    unread = LoginAttempt.unread_count()
    return render_template("security/center.html", attempts=attempts, unread=unread, page="security")


@security_bp.route("/statut/<int:attempt_id>", methods=["POST"])
@login_required
@role_required("parametres_voir")
def set_statut(attempt_id):
    from extensions import db
    import json
    data = request.get_json()
    attempt = LoginAttempt.query.get_or_404(attempt_id)
    attempt.statut = data.get("statut", attempt.statut)
    attempt.vue_par_admin = 1
    db.session.commit()
    return jsonify({"status": "ok"})


@security_bp.route("/mark-read/<int:attempt_id>", methods=["POST"])
@login_required
@role_required("parametres_voir")
def mark_read(attempt_id):
    from extensions import db
    attempt = LoginAttempt.query.get_or_404(attempt_id)
    attempt.vue_par_admin = 1
    db.session.commit()
    return jsonify({"status": "ok"})
