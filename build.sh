#!/usr/bin/env bash
# exit on error

echo "Starting build"

set -o errexit

pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input --settings=ecommerce_proj.settings.prod

# Flush database: WARNING - this deletes all data
echo "from django.db import connection; cursor = connection.cursor(); cursor.execute('DROP SCHEMA public CASCADE; CREATE SCHEMA public;')" | python manage.py shell --settings=ecommerce_proj.settings.prod

# Apply fresh migrations
python manage.py migrate --settings=ecommerce_proj.settings.prod

# Load new data from JSON fixture
python manage.py loaddata data.json --settings=ecommerce_proj.settings.prod
