from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from .models import CustomUser

admin.site.register(CustomUser, UserAdmin)
