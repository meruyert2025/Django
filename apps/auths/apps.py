# Django modules
from django.apps import AppConfig


class AuthsConfig(AppConfig):
    """Auths application configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.auths"
    verbose_name = "Authentication"
