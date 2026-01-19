#!/usr/bin/env bash
# exit on error

echo "Starting build"

set -o errexit

rm -rf staticfiles

pip install -r requirements.txt

python manage.py collectstatic --no-input --settings=ecommerce_proj.settings.prod
python manage.py migrate --settings=ecommerce_proj.settings.prod

# echo "Uploading json data"

# import data.json file
# python manage.py loaddata data.json --settings=ecommerce_proj.settings.prod