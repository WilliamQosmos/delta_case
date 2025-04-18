FROM python:3.11-slim

WORKDIR /app/

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./app /app/app
COPY ./migrations /app/migrations
COPY alembic.ini /app/alembic.ini

RUN mkdir -p /app/logs

CMD [ "sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers" ]

