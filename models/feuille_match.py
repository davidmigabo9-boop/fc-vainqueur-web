import json
from datetime import datetime
from extensions import db


class FeuilleDeMatch(db.Model):
    __tablename__ = "feuilles_de_match"

    id = db.Column(db.Integer, primary_key=True)
    date_match = db.Column(db.String(20), nullable=False)
    heure_match = db.Column(db.String(10), default="")
    lieu = db.Column(db.String(200), default="")
    adversaire = db.Column(db.String(200), nullable=False)
    score_fcv = db.Column(db.Integer, default=0)
    score_adv = db.Column(db.Integer, default=0)
    composition_json = db.Column(db.Text, default="[]")
    titulaires_json = db.Column(db.Text, default="[]")
    remplacants_json = db.Column(db.Text, default="[]")
    tactique = db.Column(db.Text, default="")
    blessures = db.Column(db.Text, default="")
    suspensions = db.Column(db.Text, default="")
    equipements = db.Column(db.Text, default="")
    notes = db.Column(db.Text, default="")
    statut = db.Column(db.String(20), default="planifie")
    cree_par = db.Column(db.Integer, default=0)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    def get_titulaires(self):
        try:
            return json.loads(self.titulaires_json)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_titulaires(self, liste):
        self.titulaires_json = json.dumps(liste)

    def get_remplacants(self):
        try:
            return json.loads(self.remplacants_json)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_remplacants(self, liste):
        self.remplacants_json = json.dumps(liste)

    @staticmethod
    def get_all():
        return FeuilleDeMatch.query.order_by(FeuilleDeMatch.date_match.desc()).all()

    @staticmethod
    def get_recent(n):
        return FeuilleDeMatch.query.order_by(FeuilleDeMatch.date_match.desc()).limit(n).all()
