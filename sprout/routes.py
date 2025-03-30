import uuid

from datetime import datetime

from flask import Blueprint, request, jsonify
from sprout.extensions import db
from sprout.models import Job, Model, ModelFile, TrainingInfo
from sprout.schemas import JobSchema
from sprout.isolation_forest.model import predict_with_isolation_forest, train_isolation_forest_model

job_schema = JobSchema()
jobs_schema = JobSchema(many=True)

job_bp = Blueprint('job_bp', __name__)
ai_bp = Blueprint('ai_bp', __name__)

BUCKET = "minio://health/"

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


@ai_bp.route('/ai/predict', methods=['POST'])
def predict():
    """
    API endpoint to detect anomalies in new data.
    """
    data = request.get_json()
    model_id_value = data.get("model_id")
    model = ModelFile.query.filter_by(model_id=model_id_value, file_type="model").first()
    scaler = ModelFile.query.filter_by(model_id=model_id_value, file_type="scaler").first()
    training_data = data.get("training_data")
    model_path = model.file_path.replace(BUCKET, "")
    scaler_path = scaler.file_path.replace(BUCKET, "")

    predict_result = predict_with_isolation_forest(model_path, training_data, scaler_path)
    return jsonify({
        'predict_result': predict_result.tolist(),
    }), 202


@ai_bp.route('/ai/train', methods=['POST'])
def train():
    """
    API endpoint to train model.
    """
    file_path = './kuka_axis_run_info_1345880_202412231603.csv'
    result = train_isolation_forest_model(file_path)

    model_filename = result["model_filename"]
    scaler_filename = result["scaler_filename"]
    model_size = result["model_size"]
    model_hash = result["model_hash"]
    scaler_size = result["scaler_size"]
    scaler_hash = result["scaler_hash"]
    # Only extract following params and save.
    keys_to_extract = {'contamination', 'n_estimators', 'random_state'}
    params = result["model"].get_params()
    filtered_params = {key: params[key] for key in keys_to_extract}
    new_model = Model(
        name="IsolationForest",
        robot_id="robot_001",
        description="One more model added",
        created_at=datetime.now()
    )

    new_training = TrainingInfo(
        model=new_model,
        robot_id=new_model.robot_id,
        hyperparameter=filtered_params,
        training_status="complete",
        created_at=datetime.now()
    )

    file_path = BUCKET  + model_filename
    new_model_file = ModelFile(
        model=new_model,
        file_name=model_filename,
        file_type="model",
        file_path=file_path,
        file_size=model_size,
        file_format="joblib",
        file_hash=model_hash,
        created_at=datetime.now()
    )

    file_path = BUCKET + scaler_filename
    new_scaler_file = ModelFile(
        model=new_model,
        file_name=scaler_filename,
        file_type="scaler",
        file_path=file_path,
        file_size=scaler_size,
        file_format="joblib",
        file_hash=scaler_hash,
        created_at=datetime.now()
    )

    db.session.add(new_model)
    db.session.add(new_training)
    db.session.add(new_model_file)
    db.session.add(new_scaler_file)
    db.session.commit()

    return jsonify({
        'train_result': "success",
        'model_id': new_model.model_id,
    }), 202


# API used for test
@ai_bp.route('/ai/get', methods=['GET'])
def get():
    models = ModelFile.query.all()

    for model in models:
        print(model.model_id)

    return jsonify({"message": "Done"}), 200
