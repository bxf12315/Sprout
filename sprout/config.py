import os

from celery.schedules import crontab


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://sprout_admin:sprout_pwd@127.0.0.1:5432/sprout_model')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MINIO_URI = os.getenv('MINIO_URI',"127.0.0.1:9000")
    MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY',"yAXD3K1ubErUUhGpMqYB")
    MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY',"0txucWYIqpDLUf2R12gjHxrZld2ZNoKiLBtgPe1H")
    broker_url = 'redis://127.0.0.1:6379/0'
    result_backend = 'redis://127.0.0.1:6379/0'
    beat_schedule = {
    'run-task-every-2-minutes': {
        'task': 'sprout.celery_worker.scheduled_task',
        'schedule': crontab(minute='*/2'),
    },
}
