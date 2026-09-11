FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "python -m scripts.wait_for_db && alembic upgrade head && python -m scripts.bootstrap_admin && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
