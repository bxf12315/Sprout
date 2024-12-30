# Sprout

## Development

Setup virtual environment and install the requirements.

```sh
python3 -m venv venv
pip3 install -r requirements.txt
```

Setup flask app and celery worker/beat
```sh
python3 app.py
celery -A celery_worker.celery worker --loglevel=info
celery -A celery_worker.celery beat --loglevel=info
```
