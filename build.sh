echo "Starting build"

set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input --settings=ecommerce_proj.settings.prod

# Safer way to reset (preserves schema but clears data)
python manage.py flush --no-input --settings=ecommerce_proj.settings.prod

# Run migrations again
python manage.py migrate --settings=ecommerce_proj.settings.prod

# Load your cleaned data (only custom app data)
python manage.py loaddata data.json --settings=ecommerce_proj.settings.prod
