#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting environment setup for HtZkaediHealingSolution..."

# 1. Navigate to project directory
cd /mnt/b/project_plot/HtZkaediHealingSolution

# 2. Create a virtual environment
python3 -m venv venv
echo "Virtual environment created."

# 3. Activate the virtual environment
source venv/bin/activate
echo "Virtual environment activated."

# 4. Upgrade pip
pip install --upgrade pip
echo "pip upgraded."

# 5. Install dependencies
pip install -r requirements.txt
echo "Dependencies installed."

# 6. Set up environment variables
if [ ! -f .env ]; then
    cp .env.example .env
    echo ".env file created from .env.example."
    echo "Please edit the .env file to set your environment variables."
else
    echo ".env file already exists. Skipping copy."
fi

# 7. Initialize the database
docker-compose up -d db
echo "Database service started."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 10

# Run migrations
alembic upgrade head
echo "Database migrations applied."

# 8. Seed initial data
python scripts/seed_data.py
echo "Initial data seeded."

# 9. Start the application
docker-compose up -d web
echo "Web service started."

echo "Environment setup completed successfully!"
