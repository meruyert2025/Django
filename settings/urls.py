# Third-party modules
from decouple import config

# Django modules
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path(config("BLOG_ADMIN_URL", default="admin/", cast=str), admin.site.urls),
]
