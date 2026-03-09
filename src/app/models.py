from .models.db import db


class MemoryEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    role = db.Column(db.String(32), nullable=False)  # user / assistant / system
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<MemoryEntry {self.id} {self.timestamp} {self.role}>"
