# src/soulprint_forge/config.py
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))     # …/src/soulprint_forge

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")

    # ->  instance/soulprint.db   (always write-able)
    SQLALCHEMY_DATABASE_URI = (
        os.getenv("DATABASE_URI")
        or "sqlite:///" + os.path.join(BASE_DIR, "..", "instance", "soulprint.db")
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # uploads lives at repo/uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "..", "uploads")
