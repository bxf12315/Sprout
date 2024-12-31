FROM python:3.9-slim as builder

WORKDIR /sprut

COPY . /sprut

RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.9-alpine

WORKDIR /sprut

COPY --from=builder /sprut /sprut

EXPOSE 5000

CMD ["python", "app.py"]