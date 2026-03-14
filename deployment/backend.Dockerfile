FROM python:3.11-slim

WORKDIR /app

COPY backend/pyproject.toml /app/backend/pyproject.toml
COPY backend/README.md /app/backend/README.md
COPY backend/app /app/backend/app
COPY data /app/data

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir /app/backend

WORKDIR /app/backend

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

