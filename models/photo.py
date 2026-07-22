from datetime import datetime
from extensions import db


class Photo(db.Model):
    __tablename__ = "photos"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    titre = db.Column(db.String(200), default="")
    ordre = db.Column(db.Integer, default=0)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def get_all():
        return Photo.query.order_by(Photo.ordre.asc(), Photo.date_creation.desc()).all()
