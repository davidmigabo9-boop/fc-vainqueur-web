from datetime import datetime
from extensions import db


class Joueur(db.Model):
    __tablename__ = "joueurs"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    postnom = db.Column(db.String(100), default="")
    prenom = db.Column(db.String(100), nullable=False)
    numero = db.Column(db.Integer, default=0)
    poste = db.Column(db.String(50), default="")
    date_naissance = db.Column(db.String(20), default="")
    adresse = db.Column(db.String(200), default="")
    telephone = db.Column(db.String(30), default="")
    email = db.Column(db.String(120), default="")
    date_arrivee = db.Column(db.String(20), default="")
    date_inscription = db.Column(db.String(20), default="")
    photo = db.Column(db.String(200), default="")
    observations = db.Column(db.Text, default="")
    actif = db.Column(db.Integer, default=1)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    contributions = db.relationship("Contribution", backref="joueur", lazy=True,
                                    cascade="all, delete-orphan")

    def calculer_age(self):
        if self.date_naissance:
            try:
                naissance = datetime.strptime(self.date_naissance, "%Y-%m-%d")
                today = datetime.now()
                age = today.year - naissance.year
                if (today.month, today.day) < (naissance.month, naissance.day):
                    age -= 1
                return age
            except ValueError:
                return 0
        return 0

    def total_contributions(self):
        return sum(c.montant for c in self.contributions)

    def get_initials(self):
        p = (self.prenom or "").strip()
        n = (self.nom or "").strip()
        if p and n:
            return (p[0] + n[0]).upper()
        if p:
            return p[0].upper()
        if n:
            return n[0].upper()
        return "?"

    @staticmethod
    def total_count():
        return Joueur.query.filter_by(actif=1).count()

    @staticmethod
    def active_joueurs():
        return Joueur.query.filter_by(actif=1).order_by(Joueur.nom, Joueur.prenom).all()

    @staticmethod
    def search(terme):
        pattern = f"%{terme}%"
        return Joueur.query.filter(
            Joueur.actif == 1,
            db.or_(
                Joueur.nom.ilike(pattern), Joueur.postnom.ilike(pattern),
                Joueur.prenom.ilike(pattern), Joueur.poste.ilike(pattern),
                Joueur.telephone.ilike(pattern), Joueur.email.ilike(pattern),
            )
        ).order_by(Joueur.nom, Joueur.prenom).all()

    def __repr__(self):
        return f"<Joueur {self.prenom} {self.nom}>"


class Contribution(db.Model):
    __tablename__ = "contributions"

    id = db.Column(db.Integer, primary_key=True)
    joueur_id = db.Column(db.Integer, db.ForeignKey("joueurs.id"), nullable=False)
    montant = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), default="")
    date_contribution = db.Column(db.String(20), nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def total_general():
        from sqlalchemy import func
        result = db.session.query(func.sum(Contribution.montant)).scalar()
        return result or 0

    @staticmethod
    def search(terme):
        pattern = f"%{terme}%"
        return db.session.query(Contribution).join(Joueur).filter(
            db.or_(
                Joueur.nom.ilike(pattern), Joueur.prenom.ilike(pattern),
                Contribution.description.ilike(pattern),
            )
        ).order_by(Contribution.date_contribution.desc()).all()

    def __repr__(self):
        return f"<Contribution {self.montant} FC>"
