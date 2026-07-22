import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extensions import db, login_manager
from flask import Flask
from config import config
from datetime import datetime
from sqlalchemy import inspect, text


def create_app(config_name="development"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    @app.context_processor
    def inject_now():
        return {"now": datetime.now()}

    data_dir = app.config.get("DATA_DIR", os.path.join(app.root_path, "instance"))
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["EXPORTS_FOLDER"], exist_ok=True)
    os.makedirs(app.config["BACKUPS_FOLDER"], exist_ok=True)

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
        _migrate_columns()
        _seed_default_admin()

    return app


def _migrate_columns():
    inspector = inspect(db.engine)
    columns = [c["name"] for c in inspector.get_columns("utilisateurs")]
    if "password_visible" not in columns:
        db.session.execute(text("ALTER TABLE utilisateurs ADD COLUMN password_visible TEXT DEFAULT ''"))
        db.session.commit()
    if "joueur_id" not in columns:
        db.session.execute(text("ALTER TABLE utilisateurs ADD COLUMN joueur_id INTEGER DEFAULT NULL"))
        db.session.commit()


def _seed_default_admin():
    from models.user import Utilisateur
    admin = Utilisateur.query.filter_by(username="admin").first()
    if not admin:
        admin = Utilisateur(
            nom_complet="Super Administrateur",
            username="admin",
            role="super_administrateur",
        )
        admin.set_password("Justin.09")
        db.session.add(admin)
        db.session.commit()
    else:
        if not admin.password_visible:
            admin.password_visible = "Justin.09"
            db.session.commit()


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
