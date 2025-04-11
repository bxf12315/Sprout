# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# from flask_marshmallow import Marshmallow
# from flask_migrate import Migrate
# from sprout.config import Config
# from sprout.extensions import db, ma, make_celery
# from sprout.routes import ai_bp, job_bp


# # migrate = Migrate()

# def create_app():
#     app = Flask(__name__)
#     app.config.from_object(Config)
#     app.config["result_backend"] = Config.result_backend
#     app.config["broker_url"] = Config.broker_url
#     app.config["beat_schedule"] = Config.beat_schedule

#     # Initialize extensions
#     db.init_app(app)
#     ma.init_app(app)
#     migrate = Migrate(app, db)
#     migrate.init_app(app, db)

#     # Register blueprints and routes
#     app.register_blueprint(job_bp, url_prefix='/api')
#     app.register_blueprint(ai_bp, url_prefix='/api')

#     with app.app_context():
#         db.create_all()

#     return app

# celery = make_celery(create_app())
# celery.conf.timezone = 'UTC'
