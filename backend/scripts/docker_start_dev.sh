#!/bin/bash
set -e

echo "============================================"
echo "Starting backend development server setup..."
echo "============================================"

# Wait for database connection
echo "[1/4] Waiting for database connection at $DB_HOST:$DB_PORT..."
while ! python -c "import socket, os, sys; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(1); sys.exit(0 if s.connect_ex((os.environ.get('DB_HOST'), int(os.environ.get('DB_PORT')))) == 0 else 1)" > /dev/null 2>&1; do
    echo "  - Database is unavailable - sleeping..."
    sleep 1
done
echo "✅ Database is up!"

# Run migrations
echo "[2/4] Running database migrations..."
alembic upgrade head
echo "✅ Migrations applied!"

# Initialize database
echo "[3/4] Initializing basic data..."
python scripts/init_database.py
echo "✅ Database initialized!"

# Start application
echo "[4/4] Starting Uvicorn server..."
echo "============================================"
# Use exec to replace the shell with the uvicorn process
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

