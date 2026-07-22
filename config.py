import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "fc-vainqueur-secret-key-change-in-production")
    DATA_DIR = os.environ.get("DATA_DIR", os.path.join(BASE_DIR, "instance"))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(DATA_DIR, 'fc_vainqueur.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "photos")
    EXPORTS_FOLDER = os.path.join(BASE_DIR, "exports")
    BACKUPS_FOLDER = os.path.join(DATA_DIR, "backups")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}
    APP_NAME = "FC VAINQUEUR"
    APP_VERSION = "1.0.0"


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
