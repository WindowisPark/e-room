#!/bin/bash

echo "🚀 Running Alembic migrations..."
alembic upgrade head

echo "✅ Alembic migration complete. Starting app..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
