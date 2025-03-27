# docker/backend/Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    netcat-traditional \
    postgresql-client \
    python3-dev \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Install the app package
RUN pip install -e .

# Create entrypoint script
RUN echo '#!/bin/sh\n\
echo "Waiting for PostgreSQL..."\n\
while ! nc -z eroom-db.c5musscuevqp.ap-northeast-2.rds.amazonaws.com 5432; do\n\
    sleep 0.1\n\
done\n\
echo "PostgreSQL is ready!"\n\
\n\
echo "Running migrations..."\n\
alembic upgrade head\n\
\n\
echo "Starting FastAPI application..."\n\
uvicorn app.main:app --host 0.0.0.0 --port 8000\n\
\n\
exec "$@"' > /entrypoint.sh

RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
