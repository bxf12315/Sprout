from extensions import db
from sqlalchemy.dialects.postgresql import JSON

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(80), unique=True, nullable=False)
    params = db.Column(db.JSON, nullable=True)
    status = db.Column(db.String(50), default='PENDING')

    def __repr__(self):
        return f"<Job {self.job_id}>"
