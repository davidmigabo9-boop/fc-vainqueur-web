from datetime import datetime
from extensions import db


class Equipement(db.Model):
    __tablename__ = "equipements"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(150), nullable=False)
    categorie = db.Column(db.String(100), default="")
    description = db.Column(db.Text, default="")
    quantite = db.Column(db.Integer, default=1)
    prix = db.Column(db.Float, default=0)
    date_achat = db.Column(db.String(20), default="")
    etat = db.Column(db.String(30), default="Neuf")
    fournisseur = db.Column(db.String(150), default="")
    observations = db.Column(db.Text, default="")
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def total_quantite():
        from sqlalchemy import func
        result = db.session.query(func.sum(Equipement.quantite)).scalar()
        return result or 0

    @staticmethod
    def search(terme):
        pattern = f"%{terme}%"
        return Equipement.query.filter(
            db.or_(
                Equipement.nom.ilike(pattern), Equipement.categorie.ilike(pattern),
                Equipement.fournisseur.ilike(pattern), Equipement.description.ilike(pattern),
            )
        ).order_by(Equipement.nom).all()

    def __repr__(self):
        return f"<Equipement {self.nom}>"
