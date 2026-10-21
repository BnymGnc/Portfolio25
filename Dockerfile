FROM python:3.13.7-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STORAGE_BACKEND=postgres \
    COOKIE_SECURE=true \
    PORT=10000

WORKDIR /app/backend
COPY backend/requirements-lock.txt ./requirements-lock.txt
RUN python -m pip install --no-cache-dir -r requirements-lock.txt

# Include the existing trained models, never local users, secrets or training jobs.
COPY backend/ ./
EXPOSE 10000
CMD ["python", "serve.py"]
