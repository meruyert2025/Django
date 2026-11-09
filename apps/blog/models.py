# Django modules
from django.conf import settings
from django.db.models import (
    CASCADE,
    PROTECT,
    SET_NULL,
    CharField,
    ForeignKey,
    ManyToManyField,
    SlugField,
    TextChoices,
    TextField,
)
from django.utils.text import slugify

# Project modules
from apps.abstracts.models import AbstractBaseModel


class Category(AbstractBaseModel):
    """Category database table."""

    NAME_MAX_LEN = 100
    SLUG_MAX_LEN = 120

    name = CharField(
        max_length=NAME_MAX_LEN,
        unique=True,
        verbose_name="Name",
    )
    slug = SlugField(
        max_length=SLUG_MAX_LEN,
        unique=True,
        verbose_name="Slug",
    )

    class Meta:
        """Category metadata."""

        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    def save(self, *args: object, **kwargs: object) -> None:
        """Auto-populate slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Tag(AbstractBaseModel):
    """Tag database table."""

    NAME_MAX_LEN = 50
    SLUG_MAX_LEN = 60

    name = CharField(
        max_length=NAME_MAX_LEN,
        unique=True,
        verbose_name="Name",
    )
    slug = SlugField(
        max_length=SLUG_MAX_LEN,
        unique=True,
        verbose_name="Slug",
    )

    class Meta:
        """Tag metadata."""

        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    def save(self, *args: object, **kwargs: object) -> None:
        """Auto-populate slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Post(AbstractBaseModel):
    """Post database table."""

    TITLE_MAX_LEN = 250
    SLUG_MAX_LEN = 270

    class Status(TextChoices):
        """Status choices for Post."""

        PUBLISHED = "published", "Published"
        DRAFT = "draft", "Draft"

    title = CharField(
        max_length=TITLE_MAX_LEN,
        verbose_name="Title",
    )
    slug = SlugField(
        max_length=SLUG_MAX_LEN,
        unique=True,
        verbose_name="Slug",
    )
    body = TextField(
        verbose_name="Body",
    )
    author = ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=PROTECT,
        related_name="posts",
        verbose_name="Author",
    )
    category = ForeignKey(
        to=Category,
        on_delete=SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
        verbose_name="Category",
    )
    tags = ManyToManyField(
        to=Tag,
        blank=True,
        related_name="posts",
        verbose_name="Tags",
    )
    status = CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="Status",
    )

    class Meta:
        """Post metadata."""

        verbose_name = "Post"
        verbose_name_plural = "Posts"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.title

    def save(self, *args: object, **kwargs: object) -> None:
        """Auto-populate slug from title if not provided."""
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Comment(AbstractBaseModel):
    """Comment database table."""

    post = ForeignKey(
        to=Post,
        on_delete=CASCADE,
        related_name="comments",
        verbose_name="Post",
    )
    author = ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=PROTECT,
        related_name="comments",
        verbose_name="Author",
    )
    body = TextField(
        verbose_name="Body",
    )

    class Meta:
        """Comment metadata."""

        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Comment by {self.author} on {self.post}"
