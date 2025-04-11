import io
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from joblib import dump, load
import matplotlib.pyplot as plt
from datetime import datetime
from sprout.common.model_cache import cached_loading
from sprout.storage.storage import MinIOModelStorage


def train_isolation_forest_model(
    bucket,
    file_path,
    features,
    n_estimators=100,
    contamination=0.0001,
    random_state=42,
    model_filename=None,
):
    """
    Train an Isolation Forest model for anomaly detection using CSV data.

    Parameters:
    -----------
    file_path : str
        Path to the CSV file containing the data
    features : list, default=["torque", "drive_angle", "temperature", "current", "speed", "time"]
        List of features to use for anomaly detection
    n_estimators : int, default=100
        Number of decision trees in the ensemble
    contamination : float, default=0.0001
        Expected proportion of outliers in the dataset
    random_state : int, default=42
        Random seed for reproducibility
    model_filename : str, default=None
        Filename to save the trained model. If None, a default name with timestamp will be used.

    Returns:
    --------
    dict
        Dictionary containing the trained model, scaler, and model filename
    """

    storage = MinIOModelStorage()

    # 1. Load and preprocess data
    data = pd.read_csv(
        storage.download_model(bucket, file_path),
        na_values=[r"\N", "N", "null", "NULL", ""],
    )
    data["time"] = pd.to_datetime(data["collect_time"])
    data["hour"] = data["time"].dt.hour
    data["dayofweek"] = data["time"].dt.dayofweek
    data["is_weekend"] = data["dayofweek"].isin([5, 6]).astype(int)

    # 2. Select features
    if not features:
        features = ["torque", "temperature", "current"]

    data = data.dropna(subset=features)
    X = data[features]

    # 3. Standardize the data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 4. Initialize and train the Isolation Forest model
    isolation_forest = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=random_state,
    )
    isolation_forest.fit(X_scaled)

    # 5. Save the model
    model_filename = stamp_filename(model_filename)

    # The destination bucket and filename on the MinIO server
    bucket_name = "health"

    # Calculate anomaly scores (lower score = more anomalous)
    scores = isolation_forest.decision_function(X_scaled)

    scores_filename = model_filename.replace(".joblib", "_scores.joblib")
    scores_buffer = io.BytesIO()
    joblib.dump(scores, scores_buffer)

    storage.upload_model(scores_buffer, bucket_name, scores_filename)

    # dump(isolation_forest, model_filename)
    model_buffer = io.BytesIO()
    joblib.dump(isolation_forest, model_buffer)
    # Also save the scaler for future use
    scaler_filename = model_filename.replace(".joblib", "_scaler.joblib")
    # dump(scaler, scaler_filename)
    model_scaler_buffer = io.BytesIO()
    joblib.dump(scaler, model_scaler_buffer)

    storage.upload_model(model_buffer, bucket_name, model_filename)
    storage.upload_model(model_scaler_buffer, bucket_name, scaler_filename)

    def get_model_info(bucket_name, object_name):
        obj_stat = storage.client.stat_object(bucket_name, object_name)

        file_size = obj_stat.size  # Size in bytes
        file_hash = obj_stat.etag  # ETag (MD5 hash for small files)

        return file_size, file_hash

    model_size, model_hash = get_model_info(bucket_name, model_filename)
    scaler_size, scaler_hash = get_model_info(bucket_name, scaler_filename)
    scores_size, scores_hash = get_model_info(bucket_name, scores_filename)
    print(f"Model saved to: {model_filename}")
    print(f"Scaler saved to: {scaler_filename}")

    return {
        "model": isolation_forest,
        "scaler": scaler,
        "model_filename": model_filename,
        "scaler_filename": scaler_filename,
        "model_size": model_size,
        "model_hash": model_hash,
        "scaler_size": scaler_size,
        "scaler_hash": scaler_hash,
        "scores_filename": scores_filename,
        "scores_size": scores_size,
        "scores_hash": scores_hash,
    }


def stamp_filename(model_filename):
    if model_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        model_filename = f"isolation_forest_model_{timestamp}.joblib"
    return model_filename


def predict_with_isolation_forest(model, data_array, scaler, scores_path):
    """
    Use a trained Isolation Forest model to detect anomalies in new data

    Parameters:
    -----------
    model : object
        Trained Isolation Forest model or path to model file
    data_array : array-like
        Array containing feature data with shape (n_samples, 3), each row is [torque, temperature, current]
    scaler : object
        StandardScaler object for data normalization or path to scaler file

    Returns:
    --------
    array
        Array with shape (n_samples, 4), each row containing [torque, temperature, current, score]
    """
    storage = MinIOModelStorage()
    # isolation_forest_model = storage.download_model("health", model)
    isolation_forest = cached_loading(model, storage)
    # isolation_forest = joblib.load(storage.download_model("health", model))

    # Convert input to numpy array
    X = np.array(data_array)

    # # Check input dimensions
    # if X.ndim == 1 and len(X) == 3:
    #     # Single sample, reshape to (1, 3)
    #     X = X.reshape(1, -1)
    # elif X.ndim != 2 or X.shape[1] != 3:
    #     raise ValueError(
    #         "Input data must be a 1D array with [torque, temperature, current] or a 2D array with shape (n_samples, 3)"
    #     )

    # Load and apply scaler

    scaler = cached_loading(scaler, storage)

    X_scaled = scaler.transform(X)

    # Get binary anomaly predictions (-1 for anomalies, 1 for normal)
    anomaly_labels = isolation_forest.predict(X_scaled)

    # Calculate anomaly scores (lower score = more anomalous)
    scores = isolation_forest.decision_function(X_scaled)

    base_scores = cached_loading(scores_path, storage)

    # Calculate health score percentage (0-100, higher = healthier)
    min_score = base_scores.min()
    max_score = base_scores.max()

    health_score_percentage = (scores - min_score) / (max_score - min_score) * 100

    # Combine original features with anomaly scores and health percentage
    result = np.column_stack([X, anomaly_labels, scores, health_score_percentage])

    return result
