# Python modules
import json
from typing import Any

# Django modules
from django.db.models import Count
from django.http import HttpRequest

# Project modules
from apps.auths.models import User
from apps.blog.models import Category, Comment, Post
from settings.conf import ENV_ID


def environment_callback(request: HttpRequest) -> list[str]:
    """
    Return environment badge and color.
    Local is orange (warning), Production is red (danger).
    """
    if ENV_ID == "prod":
        return ["Production", "danger"]
    return ["Local", "warning"]


def drafts_badge(request: HttpRequest) -> str:
    """Return count of draft posts as badge in navigation sidebar."""
    draft_count: int = Post.objects.filter(status=Post.Status.DRAFT).count()
    return str(draft_count)


def dashboard_callback(request: HttpRequest, context: dict[str, Any]) -> dict[str, Any]:
    """
    Compute analytics for the Unfold admin dashboard.
    Counts and aggregations are performed directly in the database.
    """
    total_users: int = User.objects.count()
    total_posts: int = Post.objects.count()
    published_posts_count: int = Post.objects.filter(status=Post.Status.PUBLISHED).count()
    draft_posts_count: int = Post.objects.filter(status=Post.Status.DRAFT).count()
    total_comments: int = Comment.objects.count()

    if total_posts > 0:
        pub_pct: float = round((published_posts_count / total_posts) * 100, 1)
        draft_pct: float = round((draft_posts_count / total_posts) * 100, 1)
    else:
        pub_pct = 0.0
        draft_pct = 0.0

    # Number of posts per category (for bar chart)
    category_stats = (
        Category.objects.annotate(posts_count=Count("posts"))
        .order_by("-posts_count")
    )
    cat_labels: list[str] = [c.name for c in category_stats]
    cat_data: list[int] = [c.posts_count for c in category_stats]

    category_chart_data: str = json.dumps({
        "labels": cat_labels,
        "datasets": [
            {
                "label": "Posts",
                "data": cat_data,
                "backgroundColor": "#10b981",
                "borderRadius": 6,
            }
        ],
    })

    # Top 5 authors by number of posts (for table)
    top_authors = (
        User.objects.annotate(posts_count=Count("posts"))
        .order_by("-posts_count")[:5]
    )
    authors_rows: list[list[str]] = [
        [
            author.get_full_name() or "—",
            author.email,
            str(author.posts_count),
        ]
        for author in top_authors
    ]

    context.update({
        "total_users": total_users,
        "published_posts_count": published_posts_count,
        "draft_posts_count": draft_posts_count,
        "total_comments": total_comments,
        "published_percentage": int(pub_pct),
        "published_percentage_text": f"{pub_pct}%",
        "draft_percentage": int(draft_pct),
        "draft_percentage_text": f"{draft_pct}%",
        "category_chart_data": category_chart_data,
        "authors_table": {
            "headers": ["Author", "Email", "Posts"],
            "rows": authors_rows,
        },
    })

    return context
