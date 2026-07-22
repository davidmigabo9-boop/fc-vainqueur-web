from datetime import datetime
from extensions import db


class Budget(db.Model):
    __tablename__ = "budget"

    id = db.Column(db.Integer, primary_key=True)
    type_operation = db.Column(db.String(20), nullable=False)
    motif = db.Column(db.String(200), nullable=False)
    montant = db.Column(db.Float, nullable=False)
    responsable = db.Column(db.String(100), default="")
    date_operation = db.Column(db.String(20), nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def total_recettes():
        from sqlalchemy import func
        result = db.session.query(func.sum(Budget.montant)).filter_by(type_operation="recette").scalar()
        return result or 0

    @staticmethod
    def total_depenses():
        from sqlalchemy import func
        result = db.session.query(func.sum(Budget.montant)).filter_by(type_operation="depense").scalar()
        return result or 0

    @staticmethod
    def solde():
        return Budget.total_recettes() - Budget.total_depenses()

    @staticmethod
    def recettes_mois(mois, annee):
        from sqlalchemy import func
        result = db.session.query(func.sum(Budget.montant)).filter(
            Budget.type_operation == "recette",
            db.extract("month", Budget.date_operation) == mois,
            db.extract("year", Budget.date_operation) == annee,
        ).scalar()
        return result or 0

    @staticmethod
    def depenses_mois(mois, annee):
        from sqlalchemy import func
        result = db.session.query(func.sum(Budget.montant)).filter(
            Budget.type_operation == "depense",
            db.extract("month", Budget.date_operation) == mois,
            db.extract("year", Budget.date_operation) == annee,
        ).scalar()
        return result or 0

    @staticmethod
    def get_par_mois():
        from sqlalchemy import func
        rows = db.session.query(
            func.strftime("%Y-%m", Budget.date_operation).label("mois"),
            Budget.type_operation,
            func.sum(Budget.montant).label("total"),
        ).group_by("mois", Budget.type_operation).order_by("mois").all()
        return rows

    @staticmethod
    def search(terme):
        pattern = f"%{terme}%"
        return Budget.query.filter(
            db.or_(Budget.motif.ilike(pattern), Budget.responsable.ilike(pattern))
        ).order_by(Budget.date_operation.desc()).all()

    def __repr__(self):
        return f"<Budget {self.type_operation} {self.montant}>"
