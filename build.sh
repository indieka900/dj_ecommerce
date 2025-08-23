#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input --settings=ecommerce_proj.settings.prod
python manage.py makemigrations --settings=ecommerce_proj.settings.prod
python manage.py migrate --settings=ecommerce_proj.settings.prod