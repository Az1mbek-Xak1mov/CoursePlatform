#!/bin/bash
# Production deployment script for IlmSpace

set -e

echo "🚀 Starting IlmSpace deployment..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Collect static files
echo "📦 Collecting static files..."
uv sync
uv run python manage.py collectstatic --noinput

# Run migrations
echo "🔄 Running database migrations..."
uv run python manage.py migrate --noinput

# Start Gunicorn
echo "🌐 Starting Gunicorn server..."
uv run gunicorn CoursePlatform.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${GUNICORN_WORKERS:-3} \
    --timeout ${GUNICORN_TIMEOUT:-120} \
    --log-level info \
    --access-logfile - \
    --error-logfile -
