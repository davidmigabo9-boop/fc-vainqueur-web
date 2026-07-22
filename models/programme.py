from datetime import datetime
from extensions import db


class Programme(db.Model):
    __tablename__ = "programmes"

    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    lieu = db.Column(db.String(200), nullable=False)
    date_evenement = db.Column(db.String(20), nullable=False)
    heure = db.Column(db.String(10), nullable=False)
    description = db.Column(db.Text, default="")
    actif = db.Column(db.Integer, default=1)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def get_upcoming():
        return Programme.query.filter_by(actif=1).order_by(Programme.date_evenement.desc()).all()
