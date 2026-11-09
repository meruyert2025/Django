# Python modules
from typing import Any

# Third-party modules
from unfold.forms import (
    AdminPasswordChangeForm,
    UserChangeForm as UnfoldUserChangeForm,
    UserCreationForm as UnfoldUserCreationForm,
)

# Django modules
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserCreationForm(UnfoldUserCreationForm):
    """Form used to create new users in the Unfold admin."""

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name")

    def clean_email(self) -> str:
        """Validate email uniqueness."""
        email: str = self.cleaned_data.get("email", "").lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email


class CustomUserChangeForm(UnfoldUserChangeForm):
    """Form used to edit existing users in the Unfold admin."""

    class Meta:
        model = User
        fields = "__all__"


class CustomAdminPasswordChangeForm(AdminPasswordChangeForm):
    """Password change form for administrators."""

    pass
