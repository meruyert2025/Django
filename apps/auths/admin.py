# Python modules
from typing import Any

# Third-party modules
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import BooleanRadioFilter
from unfold.decorators import action, display

# Django modules
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count, QuerySet
from django.http import HttpRequest

# Project modules
from apps.auths.forms import (
    CustomAdminPasswordChangeForm,
    CustomUserChangeForm,
    CustomUserCreationForm,
)
from apps.auths.models import User

# Re-register Group with Unfold to maintain consistent UI
admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(ModelAdmin):
    """Group admin class configuration with Unfold."""

    list_display = ("name",)
    search_fields = ("name",)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    """
    User model admin configuration extending Unfold ModelAdmin.
    Configured for email authentication without username field.
    """

    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    change_password_form = CustomAdminPasswordChangeForm

    ordering = ("-created_at",)
    list_display = (
        "display_header",
        "is_active_label",
        "is_staff_label",
        "display_posts_count",
    )
    list_display_links = ("display_header",)

    list_filter = (
        ("is_active", BooleanRadioFilter),
        ("is_staff", BooleanRadioFilter),
    )
    list_filter_submit = True

    search_fields = (
        "email",
        "first_name",
        "last_name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "deleted_at",
        "last_login",
    )

    fieldsets = (
        (
            "Personal info",
            {
                "classes": ["tab"],
                "fields": (
                    "email",
                    ("first_name", "last_name"),
                    "password",
                ),
            },
        ),
        (
            "Permissions",
            {
                "classes": ["tab"],
                "fields": (
                    ("is_active", "is_staff", "is_superuser"),
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Important dates",
            {
                "classes": ["tab"],
                "fields": (
                    "last_login",
                    "created_at",
                    "updated_at",
                    "deleted_at",
                ),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ["wide"],
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    actions = (
        "activate_users",
        "deactivate_users",
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Annotate post counts to prevent N+1 queries."""
        return (
            super()
            .get_queryset(request)
            .annotate(posts_count=Count("posts"))
        )

    @display(description="User", header=True)
    def display_header(self, obj: User) -> tuple[str, str, str]:
        """Header column with full name, email, and initials in a circle."""
        full_name: str = obj.get_full_name() or obj.email
        email: str = obj.email
        initials: str = (
            f"{obj.first_name[:1]}{obj.last_name[:1]}".upper()
            if obj.first_name or obj.last_name
            else obj.email[:2].upper()
        )
        return full_name, email, initials

    @display(
        description="Active",
        label={
            True: "success",
            False: "danger",
        },
    )
    def is_active_label(self, obj: User) -> tuple[bool, str]:
        """Colored label indicating active status."""
        return obj.is_active, "Active" if obj.is_active else "Inactive"

    @display(
        description="Staff status",
        label={
            True: "info",
            False: "warning",
        },
    )
    def is_staff_label(self, obj: User) -> tuple[bool, str]:
        """Colored label indicating staff status."""
        return obj.is_staff, "Staff" if obj.is_staff else "Regular"

    @display(description="Posts", ordering="posts_count")
    def display_posts_count(self, obj: User) -> int:
        """Sortable posts count column."""
        return getattr(obj, "posts_count", 0)

    @action(description="Activate selected users")
    def activate_users(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Bulk action to activate selected users."""
        updated: int = queryset.update(is_active=True)
        self.message_user(
            request,
            f"Successfully activated {updated} user(s).",
            messages.SUCCESS,
        )

    @action(description="Deactivate selected users")
    def deactivate_users(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Bulk action to deactivate selected users."""
        updated: int = queryset.update(is_active=False)
        self.message_user(
            request,
            f"Successfully deactivated {updated} user(s).",
            messages.SUCCESS,
        )
