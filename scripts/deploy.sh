#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting deployment to Heroku..."

# 1. Log in to Heroku
heroku login

# 2. Create a Heroku app if not already created
APP_NAME="htzkhealingdashboard"
heroku apps:create $APP_NAME || echo "Heroku app $APP_NAME already exists."

# 3. Add PostgreSQL add-on
heroku addons:create heroku-postgresql:hobby-dev --app $APP_NAME || echo "PostgreSQL add-on already exists."

# 4. Set environment variables
heroku config:set SECRET_KEY=your_secret_key_here API_KEY=your_api_key_here --app $APP_NAME

# 5. Push code to Heroku
git push heroku main

# 6. Run migrations on Heroku
heroku run alembic upgrade head --app $APP_NAME

# 7. Seed data on Heroku
heroku run python scripts/seed_data.py --app $APP_NAME

# 8. Open the app
heroku open --app $APP_NAME

echo "Deployment to Heroku completed successfully!"
