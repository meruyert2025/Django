# Python modules
from typing import Any

# Third-party modules
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    AutocompleteSelectFilter,
    ChoicesDropdownFilter,
    MultipleRelatedDropdownFilter,
    RangeDateTimeFilter,
    RelatedDropdownFilter,
)
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.decorators import action, display
from unfold.sections import TableSection

# Django modules
from django.contrib import admin, messages
from django.db import models
from django.db.models import Count, QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse

# Project modules
from apps.blog.models import Category, Comment, Post, Tag


class PostTableSection(TableSection):
    """Collapsible section displaying category posts."""

    verbose_name = "Category Posts"
    related_name = "posts"
    fields = ["title", "status", "created_at"]


class CommentTableSection(TableSection):
    """Collapsible section displaying post comments."""

    verbose_name = "Post Comments"
    related_name = "comments"
    fields = ["author", "body", "created_at"]


class CommentInline(TabularInline):
    """Inline comments displayed in a tab within the Post changeform."""

    model = Comment
    tab = True
    per_page = 10
    extra = 0
    fields = ("author", "body", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("author",)


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    """Category model admin with post count aggregation and collapsible posts."""

    list_display = (
        "name",
        "slug",
        "display_posts_count",
    )
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    list_sections = [PostTableSection]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Annotate posts count and prefetch posts in one database query."""
        return (
            super()
            .get_queryset(request)
            .prefetch_related("posts")
            .annotate(posts_count=Count("posts"))
        )

    @display(description="Posts", ordering="posts_count")
    def display_posts_count(self, obj: Category) -> int:
        """Return annotated post count."""
        return getattr(obj, "posts_count", 0)


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    """Tag model admin with post count aggregation."""

    list_display = (
        "name",
        "slug",
        "display_posts_count",
    )
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Annotate posts count in one database query."""
        return (
            super()
            .get_queryset(request)
            .annotate(posts_count=Count("posts"))
        )

    @display(description="Posts", ordering="posts_count")
    def display_posts_count(self, obj: Tag) -> int:
        """Return annotated post count."""
        return getattr(obj, "posts_count", 0)


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    """Comment model admin with autocomplete filters and N+1 prevention."""

    BODY_TRUNCATE_LEN = 50

    list_display = (
        "post",
        "author",
        "shortened_body",
        "created_at",
    )
    list_select_related = (
        "post",
        "author",
    )
    search_fields = (
        "body",
        "author__email",
        "post__title",
    )
    autocomplete_fields = (
        "post",
        "author",
    )
    list_filter = (
        ("post", AutocompleteSelectFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    )
    list_filter_submit = True

    @display(description="Body")
    def shortened_body(self, obj: Comment) -> str:
        """Return truncated comment body."""
        if len(obj.body) > self.BODY_TRUNCATE_LEN:
            return f"{obj.body[:self.BODY_TRUNCATE_LEN]}..."
        return obj.body


@admin.register(Post)
class PostAdmin(ModelAdmin):
    """
    Post model admin showcase with custom actions, WYSIWYG editor,
    autocomplete fields, tabs, dropdowns, and collapsible comments.
    """

    warn_unsaved_form = True

    formfield_overrides = {
        models.TextField: {
            "widget": WysiwygWidget,
        },
    }

    inlines = [CommentInline]
    list_sections = [CommentTableSection]

    list_display = (
        "display_header",
        "status_label",
        "category",
        "display_tags",
        "display_comments_count",
        "created_at",
    )
    list_display_links = ("display_header",)

    list_select_related = (
        "author",
        "category",
    )
    list_prefetch_related = ("tags",)

    search_fields = (
        "title",
        "body",
        "author__email",
    )

    autocomplete_fields = (
        "author",
        "category",
        "tags",
    )
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = (
        "created_at",
        "updated_at",
    )

    list_filter = (
        ("status", ChoicesDropdownFilter),
        ("category", RelatedDropdownFilter),
        ("tags", MultipleRelatedDropdownFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    )
    list_filter_submit = True

    fieldsets = (
        (
            "Content",
            {
                "classes": ["tab"],
                "fields": (
                    "title",
                    "slug",
                    "body",
                ),
            },
        ),
        (
            "Classification",
            {
                "classes": ["tab"],
                "fields": (
                    "category",
                    "tags",
                    "status",
                ),
            },
        ),
        (
            "Meta",
            {
                "classes": ["tab"],
                "fields": (
                    "author",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    actions = (
        "publish_selected",
        "move_to_drafts",
    )
    actions_row = (
        "toggle_publish",
    )
    actions_list = (
        "publish_all_drafts",
    )
    actions_detail = (
        "open_comments",
    )
    actions_submit_line = (
        "save_and_publish",
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Annotate comments count and prefetch relationships to eliminate N+1 queries."""
        return (
            super()
            .get_queryset(request)
            .select_related("author", "category")
            .prefetch_related("tags", "comments__author")
            .annotate(comments_count=Count("comments"))
        )

    @display(description="Post", header=True)
    def display_header(self, obj: Post) -> tuple[str, str]:
        """Header column showing post title and author name/email."""
        author_name: str = obj.author.get_full_name() or obj.author.email
        return obj.title, f"By {author_name}"

    @display(
        description="Status",
        label={
            Post.Status.PUBLISHED: "success",
            Post.Status.DRAFT: "warning",
        },
    )
    def status_label(self, obj: Post) -> tuple[str, str]:
        """Colored label for post publication status."""
        return obj.status, obj.get_status_display()

    @display(description="Tags", dropdown=True)
    def display_tags(self, obj: Post) -> dict[str, Any]:
        """Dropdown column displaying post tags without N+1 query."""
        tags: list[Tag] = list(obj.tags.all())
        return {
            "title": f"{len(tags)} tag(s)" if tags else "No tags",
            "items": [{"title": tag.name} for tag in tags],
        }

    @display(description="Comments", ordering="comments_count")
    def display_comments_count(self, obj: Post) -> int:
        """Sortable comments count column."""
        return getattr(obj, "comments_count", 0)

    # Bulk actions
    @action(description="Publish selected posts")
    def publish_selected(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Bulk action to publish selected posts."""
        updated: int = queryset.update(status=Post.Status.PUBLISHED)
        self.message_user(
            request,
            f"Successfully published {updated} post(s).",
            messages.SUCCESS,
        )

    @action(description="Move selected posts to drafts")
    def move_to_drafts(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Bulk action to move selected posts to drafts."""
        updated: int = queryset.update(status=Post.Status.DRAFT)
        self.message_user(
            request,
            f"Successfully moved {updated} post(s) to drafts.",
            messages.SUCCESS,
        )

    # Row action
    @action(description="Publish / Unpublish", url_path="toggle-publish")
    def toggle_publish(self, request: HttpRequest, object_id: int) -> HttpResponse:
        """Toggle post status between published and draft."""
        post: Post = self.get_object(request, object_id)
        if post.status == Post.Status.PUBLISHED:
            post.status = Post.Status.DRAFT
            msg: str = f"Post '{post.title}' moved to drafts."
        else:
            post.status = Post.Status.PUBLISHED
            msg = f"Post '{post.title}' published."
        post.save(update_fields=["status", "updated_at"])
        self.message_user(request, msg, messages.SUCCESS)
        return redirect(reverse("admin:blog_post_changelist"))

    # List action
    @action(description="Publish all drafts", url_path="publish-all-drafts")
    def publish_all_drafts(self, request: HttpRequest) -> HttpResponse:
        """Publish all existing draft posts."""
        count: int = Post.objects.filter(status=Post.Status.DRAFT).update(
            status=Post.Status.PUBLISHED
        )
        self.message_user(
            request,
            f"Successfully published all {count} draft post(s).",
            messages.SUCCESS,
        )
        return redirect(reverse("admin:blog_post_changelist"))

    # Detail action
    @action(description="Open post's comments", url_path="comments")
    def open_comments(self, request: HttpRequest, object_id: int) -> HttpResponse:
        """Redirect to filtered comments list for this post."""
        return redirect(
            f"{reverse('admin:blog_comment_changelist')}?post__id__exact={object_id}"
        )

    # Submit line action
    @action(description="Save & publish")
    def save_and_publish(self, request: HttpRequest, obj: Post) -> None:
        """Save and immediately publish the post."""
        obj.status = Post.Status.PUBLISHED
        obj.save(update_fields=["status", "updated_at"])
        self.message_user(
            request,
            f"Post '{obj.title}' saved and published.",
            messages.SUCCESS,
        )
