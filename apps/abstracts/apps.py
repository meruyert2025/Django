# Django modules
from django.apps import AppConfig


class AbstractsConfig(AppConfig):
    """Abstracts application configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.abstracts"
    verbose_name = "Abstracts"
