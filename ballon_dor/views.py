# Add this to your ballon_dor/views.py
from django.http import JsonResponse
import cloudinary
import os


def test_cloudinary(request):
    try:
        # Check if variables are loaded
        cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME")

        # Test connection
        result = cloudinary.api.ping()

        return JsonResponse(
            {
                "status": "success",
                "cloud_name": cloud_name,
                "ping": "OK" if result.get("status") == "ok" else "Failed",
            }
        )
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)})
