import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")


def _build_mysql_uri():
    user = os.environ.get("DB_USER", "edacms_user")
    password = os.environ.get("DB_PASSWORD", "edacms_pass")
    host = os.environ.get("DB_HOST", "127.0.0.1")
    port = os.environ.get("DB_PORT", "3306")
    name = os.environ.get("DB_NAME", "edacms")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "edacms-dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = _build_mysql_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "edacms-jwt-secret-change-me")
    UPLOAD_FOLDER = UPLOAD_DIR
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB
