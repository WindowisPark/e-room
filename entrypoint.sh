#!/bin/bash
set -e

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting server on port ${PORT:-8000}..."
exec gunicorn app.main:app \
    -k uvicorn.workers.UvicornWorker \
    -b "0.0.0.0:${PORT:-8000}" \
    --workers 2 \
    --timeout 120 \
    --keep-alive 5
