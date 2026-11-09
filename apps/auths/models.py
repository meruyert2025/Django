# Python modules
from typing import Any

# Django modules
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.db.models import BooleanField, CharField, EmailField

# Project modules
from apps.abstracts.models import AbstractBaseModel


class UserManager(BaseUserManager):
    """Custom User Manager to handle user creation with email as unique identifier."""

    def __obtain_user_instance(
        self,
        email: str,
        first_name: str,
        last_name: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "User":
        """Instantiate user with normalized email and validation."""
        if not email:
            raise ValidationError(
                message="Email field is required.",
                code="email_empty",
            )
        if not first_name:
            raise ValidationError(
                message="First name is required.",
                code="first_name_empty",
            )
        if not last_name:
            raise ValidationError(
                message="Last name is required.",
                code="last_name_empty",
            )

        email = self.normalize_email(email)
        user: "User" = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            **extra_fields,
        )
        return user

    def create_user(
        self,
        email: str,
        first_name: str,
        last_name: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "User":
        """Create regular user."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        user: "User" = self.__obtain_user_instance(
            email=email,
            first_name=first_name,
            last_name=last_name,
            **extra_fields,
        )
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        first_name: str,
        last_name: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "User":
        """Create superuser for admin panel access."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            **extra_fields,
        )


class User(AbstractBaseUser, PermissionsMixin, AbstractBaseModel):
    """
    Custom user model extending AbstractBaseModel, authenticated via email.
    """

    EMAIL_MAX_LEN = 254
    FIRST_NAME_MAX_LEN = 150
    LAST_NAME_MAX_LEN = 150
    PASSWORD_MAX_LEN = 254

    email = EmailField(
        max_length=EMAIL_MAX_LEN,
        unique=True,
        db_index=True,
        verbose_name="Email address",
    )
    first_name = CharField(
        max_length=FIRST_NAME_MAX_LEN,
        verbose_name="First name",
    )
    last_name = CharField(
        max_length=LAST_NAME_MAX_LEN,
        verbose_name="Last name",
    )
    password = CharField(
        max_length=PASSWORD_MAX_LEN,
        verbose_name="Password",
    )
    is_staff = BooleanField(
        default=False,
        verbose_name="Staff status",
        help_text="Designates whether the user can log into this admin site.",
    )
    is_active = BooleanField(
        default=True,
        verbose_name="Active",
        help_text="Designates whether this user should be treated as active.",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    class Meta:
        """User table metadata."""

        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.email

    def get_full_name(self) -> str:
        """Return the first_name plus the last_name, with a space in between."""
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self) -> str:
        """Return the short name for the user."""
        return self.first_name

    @property
    def full_name(self) -> str:
        """Convenience property for full name."""
        return self.get_full_name()
