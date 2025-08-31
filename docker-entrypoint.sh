#!/bin/bash
# 🚀 LivePrecisionCalculator - Docker Entrypoint Script
# ===================================================

set -e

# Print startup banner
echo "🚀 Starting LivePrecisionCalculator Quantum Engine..."
echo "======================================================"

# Initialize database if it doesn't exist
if [ ! -f "/app/data/quantum_calculator.db" ]; then
    echo "📊 Initializing database..."
    mkdir -p /app/data
    if [ -f "/app/schema.sql" ]; then
        sqlite3 /app/data/quantum_calculator.db < /app/schema.sql
        echo "✅ Database initialized with schema"
    fi
fi

# Wait for Redis if configured
if [ "${REDIS_HOST}" ]; then
    echo "🔄 Waiting for Redis at ${REDIS_HOST}:${REDIS_PORT}..."
    while ! redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" ping > /dev/null 2>&1; do
        echo "⏳ Redis not ready, waiting..."
        sleep 2
    done
    echo "✅ Redis connection established"
fi

# Set default environment variables
export HOST=${HOST:-"0.0.0.0"}
export PORT=${PORT:-"8000"}
export WORKERS=${WORKERS:-"1"}
export LOG_LEVEL=${LOG_LEVEL:-"info"}

# Create log directory
mkdir -p /app/logs

# Start the application
echo "🎯 Starting LivePrecisionCalculator on ${HOST}:${PORT}..."
echo "🔧 Configuration:"
echo "   - Workers: ${WORKERS}"
echo "   - Log Level: ${LOG_LEVEL}"
echo "   - Redis Host: ${REDIS_HOST:-"not configured"}"
echo "   - Database: /app/data/quantum_calculator.db"
echo "======================================================"

# Production mode with Gunicorn
if [ "${ENVIRONMENT}" = "production" ]; then
    exec gunicorn live_precision_calculator:app \
        --bind "${HOST}:${PORT}" \
        --workers "${WORKERS}" \
        --worker-class uvicorn.workers.UvicornWorker \
        --log-level "${LOG_LEVEL}" \
        --access-logfile /app/logs/access.log \
        --error-logfile /app/logs/error.log \
        --preload \
        --max-requests 1000 \
        --max-requests-jitter 100 \
        --timeout 30 \
        --keep-alive 2
else
    # Development mode with Uvicorn
    exec uvicorn live_precision_calculator:app \
        --host "${HOST}" \
        --port "${PORT}" \
        --log-level "${LOG_LEVEL}" \
        --reload
fi