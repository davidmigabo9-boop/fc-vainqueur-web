from datetime import datetime
from extensions import db


class LoginAttempt(db.Model):
    __tablename__ = "login_attempts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("utilisateurs.id"), nullable=True)
    username = db.Column(db.String(100), nullable=False)
    selfie_filename = db.Column(db.String(200), default="")
    ip_address = db.Column(db.String(50), default="")
    user_agent = db.Column(db.String(300), default="")
    location = db.Column(db.String(200), default="")
    statut = db.Column(db.String(20), default="en_attente")
    vue_par_admin = db.Column(db.Integer, default=0)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def get_recent(n):
        return LoginAttempt.query.order_by(LoginAttempt.date_creation.desc()).limit(n).all()

    @staticmethod
    def get_all():
        return LoginAttempt.query.order_by(LoginAttempt.date_creation.desc()).all()

    @staticmethod
    def unread_count():
        return LoginAttempt.query.filter_by(vue_par_admin=0).count()
