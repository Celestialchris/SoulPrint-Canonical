import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "instance"))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")

    # Default DB path for local development / fresh checkout.
    SQLALCHEMY_DATABASE_URI = (
        os.getenv("DATABASE_URI")
        or "sqlite:///" + os.path.join(INSTANCE_DIR, "soulprint.db")
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # uploads lives at repo/uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "..", "uploads")
