# passenger_wsgi.py (next to manage.py)
import sys
import os

# Add your project directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set Django settings module to production
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "ballon_dor_project.settings_production"
)

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
