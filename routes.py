import uuid

from flask import Blueprint, request, jsonify
from extensions import db
from models import Job
from schemas import JobSchema

job_schema = JobSchema()
jobs_schema = JobSchema(many=True)

job_bp = Blueprint('job_bp', __name__)
ai_bp = Blueprint('ai_bp', __name__)

# Import Celery task inside the route function to avoid circular dependency
@job_bp.route('/jobs', methods=['POST'])
def create_job():
    from celery_worker import execute_job  # Import here to prevent circular import

    import time
    data = request.get_json()
    job_id = f"job_{int(time.time())}"
    new_job = Job(
        job_id=job_id,
        params=data.get('params', {})
    )
    db.session.add(new_job)
    db.session.commit()

    # Trigger Celery task
    execute_job.apply_async(args=[job_id, data.get('params', {})])

    return jsonify({"message": "Job created", "job_id": job_id}), 201

# Get all jobs
@job_bp.route('/jobs', methods=['GET'])
def get_jobs():
    all_jobs = Job.query.all()
    return jobs_schema.jsonify(all_jobs), 200

# Get a single job by ID
@job_bp.route('/jobs/<int:id>', methods=['GET'])
def get_job(id):
    job = Job.query.get_or_404(id)
    return job_schema.jsonify(job), 200

# Update a job
@job_bp.route('/jobs/<int:id>', methods=['PUT'])
def update_job(id):
    job = Job.query.get_or_404(id)
    data = request.get_json()
    job.job_id = data.get('job_id', job.job_id)
    job.params = data.get('params', job.params)
    db.session.commit()
    return job_schema.jsonify(job), 200

# Delete a job
@job_bp.route('/jobs/<int:id>', methods=['DELETE'])
def delete_job(id):
    job = Job.query.get_or_404(id)
    db.session.delete(job)
    db.session.commit()
    return jsonify({"message": "Job deleted"}), 200

# Check Job Status
@job_bp.route('/jobs/<string:job_id>', methods=['GET'])
def get_job_status(job_id):
    job = Job.query.filter_by(job_id=job_id).first()
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return job_schema.jsonify(job), 200

@ai_bp.route('/ai/run', methods=['POST'])
def run_ai_task():
    """
    API Endpoint to trigger an AI task.
    """
    from celery_worker import run_ai_job

    data = request.get_json()
    params = data.get('params', {})

    # Create a job in the database
    new_job = Job(
        job_id=str(uuid.uuid4()),
        params=params,
        status='PENDING'
    )
    db.session.add(new_job)
    db.session.commit()

    jobs = Job.query.all()
    for job in jobs:
        print(job.id, job.job_id, job.params)

    # Trigger the Celery task
    run_ai_job.apply_async(args=[new_job.id, params])

    return jsonify({
        'message': 'AI job started',
        'job_id': new_job.id
    }), 202


@ai_bp.route('/ai/status/<int:job_id>', methods=['GET'])
def get_ai_job_status(job_id):
    """
    API Endpoint to check the status of an AI task.
    """
    job = Job.query.get(job_id)
    if not job:
        return jsonify({'message': 'Job not found'}), 404

    return jsonify({
        'job_id': job.id,
        'status': job.status,
        'params': job.params
    })
