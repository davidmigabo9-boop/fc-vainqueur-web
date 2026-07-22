from datetime import datetime
from extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    username = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, default="")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def log(user_id, username, role, action, details=""):
        entry = AuditLog(
            user_id=user_id, username=username,
            role=role, action=action, details=details,
        )
        db.session.add(entry)
        db.session.commit()

    @staticmethod
    def get_recent(limit=50):
        return AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
