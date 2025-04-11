import pytest
from flask import Flask
from sprout.models import db, Model, TrainingInfo, ModelFile, Dataset
import uuid


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///:memory:"  # Use in-memory SQLite DB
    )
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://sprout_admin:sprout_pwd@localhost:5432/sprout_model'
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()  # Create tables before running tests
        yield app  # Provide the app instance to the tests


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def session(app):
    """Create a new database session for testing."""
    with app.app_context():
        yield db.session
        db.session.rollback()  # Rollback any changes after each test


def test_create_dataset(session):
    """Test creating a DataSet instance."""
    dataset = Dataset(robot_id="robot_123", file_path="minio://datasets/sample.csv")
    session.add(dataset)
    session.commit()

    retrieved_ds = Dataset.query.filter_by(robot_id="robot_123").first()
    assert retrieved_ds is not None
    assert retrieved_ds.file_path == "minio://datasets/sample.csv"


def test_create_model(session):
    """Test creating a Model instance."""
    model = Model(
        name="Test Model", robot_id="robot_123", description="Sample description"
    )
    session.add(model)
    session.commit()

    retrieved_model = Model.query.filter_by(name="Test Model").first()
    assert retrieved_model is not None
    assert retrieved_model.name == "Test Model"
    assert retrieved_model.robot_id == "robot_123"


def test_create_training_info(session):
    """Test creating a TrainingInfo instance and linking to a Model."""
    model = Model(
        name="Test Model", robot_id="robot_123", description="Sample description"
    )
    session.add(model)
    session.commit()

    training = TrainingInfo(
        model_id=model.model_id,
        robot_id="robot_123",
        hyperparameter={"n_estimators": 100},
        training_status="pending",
    )
    session.add(training)
    session.commit()

    retrieved_training = TrainingInfo.query.filter_by(model_id=model.model_id).first()
    assert retrieved_training is not None
    assert retrieved_training.model_id == model.model_id
    assert retrieved_training.training_status == "pending"


def test_create_model_file(session):
    """Test creating a ModelFile instance and linking to a Model."""
    model = Model(
        name="Test Model", robot_id="robot_123", description="Sample description"
    )
    session.add(model)
    session.commit()

    model_file = ModelFile(
        model_id=model.model_id,
        file_name="model.pkl",
        file_path="/models/model.pkl",
        file_size=1024,
        file_format="pkl",
        file_hash="abc123",
    )
    session.add(model_file)
    session.commit()

    retrieved_file = ModelFile.query.filter_by(model_id=model.model_id).first()
    assert retrieved_file is not None
    assert retrieved_file.file_name == "model.pkl"


def test_create_multiple_model_files(session):
    """Test creating multiple ModelFiles and linking to a Model."""
    model = Model(
        name="Test Model", robot_id="robot_123", description="Sample description"
    )
    session.add(model)
    session.commit()

    model_file1 = ModelFile(
        model_id=model.model_id,
        file_name="model1.pkl",
        file_path="/models/model1.pkl",
        file_size=1024,
        file_format="pkl",
        file_hash="abc123",
    )

    model_file2 = ModelFile(
        model_id=model.model_id,
        file_name="model2.pkl",
        file_path="/models/model2.pkl",
        file_size=1024,
        file_format="pkl",
        file_hash="abc123",
    )

    model_file3 = ModelFile(
        model_id=model.model_id,
        file_name="model3.pkl",
        file_path="/models/model3.pkl",
        file_size=1024,
        file_format="pkl",
        file_hash="abc123",
    )

    db.session.add_all([model_file1, model_file2, model_file3])
    db.session.commit()

    # Query files for the given model_id
    files = ModelFile.query.filter_by(model_id=model.model_id).all()

    # Assertions
    assert len(files) == 3
    assert {f.file_name for f in files} == {"model1.pkl", "model2.pkl", "model3.pkl"}


def test_update_model(session):
    """Test updating a Model instance."""
    model = Model(name="Old Name", robot_id="robot_123", description="Old description")
    session.add(model)
    session.commit()

    model.name = "New Name"
    session.commit()

    updated_model = Model.query.filter_by(model_id=model.model_id).first()
    assert updated_model.name == "New Name"


def test_delete_model(session):
    """Test deleting a Model instance."""
    model = Model(name="Test Model", robot_id="robot_123", description="To be deleted")
    session.add(model)
    session.commit()

    session.delete(model)
    session.commit()

    deleted_model = Model.query.filter_by(name="Test Model").first()
    assert deleted_model is None
