from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from permissions import has_permission, get_role_label


class Utilisateur(UserMixin, db.Model):
    __tablename__ = "utilisateurs"

    id = db.Column(db.Integer, primary_key=True)
    nom_complet = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    password_visible = db.Column(db.String(128), default="")
    role = db.Column(db.String(50), nullable=False, default="lecteur")
    joueur_id = db.Column(db.Integer, db.ForeignKey("joueurs.id"), nullable=True)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        self.password_visible = password

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def role_label(self):
        return get_role_label(self.role)

    def has_perm(self, permission):
        return has_permission(self.role, permission)

    def is_super_admin(self):
        return self.role == "super_administrateur"

    @staticmethod
    def authenticate(username, password):
        user = Utilisateur.query.filter_by(username=username).first()
        if user and user.check_password(password):
            return user
        return None

    def __repr__(self):
        return f"<Utilisateur {self.username}>"
