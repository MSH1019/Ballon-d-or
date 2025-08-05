web: python manage.py collectstatic --noinput && gunicorn 
ballon_dor_project.wsgi:application --host 0.0.0.0 --port $PORT