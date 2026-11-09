# Django modules
from django.contrib import admin

# Project modules
from apps.auths.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """User model admin."""

    list_display = ("id", "email", "first_name", "last_name", "is_staff", "is_active")
