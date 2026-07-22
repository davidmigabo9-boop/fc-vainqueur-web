import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extensions import db, login_manager
from flask import Flask
from config import config
from datetime import datetime


def create_app(config_name="development"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    @app.context_processor
    def inject_now():
        return {"now": datetime.now()}

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["EXPORTS_FOLDER"], exist_ok=True)
    os.makedirs(app.config["BACKUPS_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from models.user import Utilisateur

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Utilisateur, int(user_id))

    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.joueurs import joueurs_bp
    from routes.budget import budget_bp
    from routes.equipements import equipements_bp
    from routes.settings import settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(joueurs_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(equipements_bp)
    app.register_blueprint(settings_bp)

    with app.app_context():
        db.create_all()
        _seed_default_admin(app)

    return app


def _seed_default_admin(app):
    from models.user import Utilisateur
    admin = Utilisateur.query.filter_by(username="admin").first()
    if not admin:
        admin = Utilisateur(
            nom_complet="Super Administrateur",
            username="admin",
            role="super_administrateur",
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
