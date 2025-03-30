
CREATE TABLE models (
    model_id VARCHAR(36) PRIMARY KEY, -- 
    name VARCHAR(255) NOT NULL, -- e.g.: IsolationForest
    robot_id VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE training_info (
    training_id VARCHAR(36) PRIMARY KEY, -- 
    model_id VARCHAR(36) NOT NULL,
    robot_id VARCHAR(255) NOT NULL,
    hyperparameter JSON NOT NULL, -- e.g.: {"n_estimators":"", "contamination":""}
    training_status VARCHAR(48), -- pending, running, completed, failed, canceled
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES models(model_id)
);

CREATE TABLE model_files (
    file_id VARCHAR(36) PRIMARY KEY, -- 
    model_id  VARCHAR(36) NOT NULL,
    file_name  VARCHAR(255) NOT NULL,
    file_type  VARCHAR(48), -- training_data, model, scaler
    file_path TEXT NOT NULL,  -- e.g.: minio://bucket_name/object_name or /local_path
    file_size BIGINT,
    file_format VARCHAR(32),
    file_hash  VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (model_id) REFERENCES models(model_id)
);

INSERT INTO models (model_id, name, robot_id, description)  
VALUES 
    ('03FA28A7-9B0F-4038-B1C9-3EDA235597D3', 'IsolationForest', 'robot_001', 'Anomaly detection model');

INSERT INTO training_info (training_id, model_id, robot_id, hyperparameter, training_status, started_at, completed_at)  
VALUES 
    ('29803061-FA3B-4021-BA74-008F180D1970', '03FA28A7-9B0F-4038-B1C9-3EDA235597D3', 'robot_001', '{"n_estimators": 100, "contamination": "0.01", "random_state": 42}', 'completed', NOW(), NOW());

INSERT INTO model_files (file_id, model_id, file_name, file_type, file_path, file_size, file_format, file_hash)  
VALUES 
    ('81B9F38E-9670-4A9D-9343-E5584FCA1B4F', '03FA28A7-9B0F-4038-B1C9-3EDA235597D3', 'isolation_forest_model_20250328222612.joblib', 'model', 'minio://health/isolation_forest_model_20250328222612.joblib', 0, 'joblib', ''),
    ('C31F3DE9-7EE2-4DCB-A096-4318BE8C17CB', '03FA28A7-9B0F-4038-B1C9-3EDA235597D3', 'isolation_forest_model_20250328222612_scaler.joblib', 'scaler', 'minio://health/isolation_forest_model_20250328222612_scaler.joblib', 0, 'joblib', '');