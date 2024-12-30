import os

from celery.schedules import crontab


class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///jobs.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    broker_url = 'redis://localhost:6379/0'
    result_backend = 'redis://localhost:6379/0'
    beat_schedule = {
    'run-task-every-2-minutes': {
        'task': 'celery_worker.scheduled_task',
        'schedule': crontab(minute='*/2'),
    },
}
