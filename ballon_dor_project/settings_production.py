# Create: ballon_dor_project/settings_production.py

from .settings import *
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Add your domain (replace the * wildcard)
ALLOWED_HOSTS = ["fansaward.com", "www.fansaward.com", ".fansaward.com"]

# Database - use your Libyan Spider database details
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "fansawar_fansaward_db",  # Your Libyan Spider database name
        "USER": "fansawar_Mohamed",  # Your Libyan Spider database user name
        "PASSWORD": "!*RCc!lj#b",  # your Libyan Spider database password
        "HOST": "localhost",
        "PORT": "5432",
    }
}

# Static files (CSS, JavaScript, Images) - for production
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(
    BASE_DIR, "staticfiles"
)  # Django will collect static files here

# Media files (user uploads) - for production
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "mediafiles")  # User uploads go here

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Use your existing email configuration (already looks good!)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "mail.fansaward.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "contact@fansaward.com"
EMAIL_HOST_PASSWORD = "M1h2m3d4!"  # Keep your existing email password
DEFAULT_FROM_EMAIL = "FansAward <contact@fansaward.com>"

# Generate a new secret key for production (optional but recommended)
SECRET_KEY = "django-insecure-f%!^-35g_pm56jspzy#a4=7h&o5)r=3e2mq6wau7u93eod5z8z"

DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.getenv("CLOUDINARY_CLOUD_NAME"),
    "API_KEY": os.getenv("CLOUDINARY_API_KEY"),
    "API_SECRET": os.getenv("CLOUDINARY_API_SECRET"),
}
