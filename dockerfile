FROM python:3.9-slim as builder

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

RUN ls

CMD ["python", "app.py"]

