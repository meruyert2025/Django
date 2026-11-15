from datetime import date, timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import(
    Avg,
    Case,
    Count,
    Exists,
    F,
    Max,
    Min,
    OuterRef,
    Prefetch,
    Q,
    QuerySet,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Coalesce, Concat,TruncMonth
from django.utils import timezone
from django.utils.text import slugify
from apps.blog.models import Category, Comment, Post, Tag
User=get_user_model()
NEWEST_POSTS_LIMIT:int=5
PAGE_SIZE: int=10
EDITED_THRESHOLD_HOURS: int=1
UNCATEGORIZED_LABEL: str="Uncategorized"
ROUND_DIGITS: int=2
DEFAULT_AVG_COMMENTS: float =0.0
TOP_AUTHORS_LIMIT:int=5
POPULARITY_HOT_THRESHOLD: int = 10
POPULARITY_NORMAL_THRESHOLD: int=3
POPULARITY_HOT: str="hot"
POPULARITY_NORMAL:str="normal"
POPULARITY_QUIET: str="quiet"
FEED_LIMIT:int=50
NEWEST_TAGGED_POSTS_LIMIT: int=20
 
def categories_by_name()-> QuerySet[Category]:
    """All categories,sorted by name A-> Z."""
    return Category.objects.order_by("name")

def published_posts() -> QuerySet[Post]:
    return Post.objects.filter(status=Post.Status.PUBLISHED).order_by("-created_at")

def newest_published_posts() -> QuerySet[Post]:
    """The 5 newest published posts."""
    return Post.objects.filter(status=Post.Status.PUBLISHED).order_by("-created_at")[:NEWEST_POSTS_LIMIT]

def post_by_slug(slug: str) -> Post | None:
    """The post with this slug, or None if there is no such post."""
    return Post.objects.filter(slug=slug).first()

def active_users_count() ->int:
    """Number of active users. Staff users are not counted."""
    return User.objects.filter(is_active=True,is_staff=False).count()

def has_drafts() -> bool:
    """True if there is at least one draft posts."""
    return Post.objects.filter(status=Post.Status.DRAFT).exists()

def published_posts_page(page:int)-> QuerySet[Post]:
    """One page of published posts,newest first (10 posts per page)."""
    offset: int = (page-1)* PAGE_SIZE
    limit:int= offset+ PAGE_SIZE
    return Post.objects.filter(status=Post.Status.PUBLISHED).order_by("-created_at")[offset:limit]


def posts_with_word_in_title(word: str) -> QuerySet[Post]:
    """Posts whose title contain word. Case-insensitive."""
    return Post.objects.filter(title__icontains=word)

def users_with_email_domain(domain: str) -> QuerySet[User]:
    """User whose email ends with @ + domain."""
    return User.objects.filter(email__iendswith=f"@{domain}")

def posts_without_category() -> QuerySet[Post]:
    """Posts that have no category."""
    return Post.objects.filter(category__isnull=True)


def categories_by_slugs(slugs: list[str]) -> QuerySet[Category]:
    """Categories whose slug is in the list slugs."""
    return Category.objects.filter(slug__in=slugs)


def posts_in_month(year: int, month: int) -> QuerySet[Post]:
    """Posts created in this month of this year."""
    return Post.objects.filter(created_at__year=year, created_at__month=month)


def posts_last_days(days: int) -> QuerySet[Post]:
    """Posts created in the last days days."""
    cutoff = timezone.now() - timedelta(days=days)
    return Post.objects.filter(created_at__gte=cutoff)


def posts_between(start: date, end: date) -> QuerySet[Post]:
    """Posts created from start to end inclusive."""
    return Post.objects.filter(created_at__date__range=(start, end))

def author_published_posts(email: str) -> QuerySet[Post]:
    """Published posts of the author with this email. Case-insensitive."""
    return Post.objects.filter(status=Post.Status.PUBLISHED, author__email__iexact=email)


def posts_with_tag(tag_slug: str) -> QuerySet[Post]:
    """Posts that have the tag with this slug."""
    return Post.objects.filter(tags__slug=tag_slug)


def comments_in_category(category_slug: str) -> QuerySet[Comment]:
    """Comments on posts of the category with this slug."""
    return Comment.objects.filter(post__category__slug=category_slug)


def users_with_published_posts() -> QuerySet[User]:
    """Users who have at least one published post without duplicates."""
    return User.objects.filter(posts__status=Post.Status.PUBLISHED).distinct()


def posts_without_tags() -> QuerySet[Post]:
    """Posts that have no tags."""
    return Post.objects.filter(tags__isnull=True)


def users_without_comments() -> QuerySet[User]:
    """Users who have never written a comment."""
    return User.objects.filter(comments__isnull=True)


def posts_with_both_tags(first_slug: str, second_slug: str) -> QuerySet[Post]:
    """Posts that have both tags simultaneously."""
    return Post.objects.filter(tags__slug=first_slug).filter(tags__slug=second_slug)


def search_posts(text: str) -> QuerySet[Post]:
    """Posts that have text in title or body. Case-insensitive."""
    return Post.objects.filter(Q(title__icontains=text) | Q(body__icontains=text))


def published_posts_missing_info() -> QuerySet[Post]:
    """Published posts that have no category or no tags without duplicates."""
    return (
        Post.objects.filter(status=Post.Status.PUBLISHED)
        .filter(Q(category__isnull=True) | Q(tags__isnull=True))
        .distinct()
    )


def edited_posts() -> QuerySet[Post]:
    """Posts that were edited more than 1 hour after creation."""
    threshold = timedelta(hours=EDITED_THRESHOLD_HOURS)
    return Post.objects.filter(updated_at__gt=F("created_at") + threshold)


def comments_by_post_author() -> QuerySet[Comment]:
    """Comments that the author wrote under their own post."""
    return Comment.objects.filter(author=F("post__author"))


def comments_before_post() -> QuerySet[Comment]:
    """Comments created before their post (integrity verification)."""
    return Comment.objects.filter(created_at__lt=F("post__created_at"))
def published_authors_emails() -> list[str]:
    """Unique emails of authors with published posts, sorted A -> Z."""
    return list(
        User.objects.filter(posts__status=Post.Status.PUBLISHED)
        .order_by("email")
        .values_list("email", flat=True)
        .distinct()
    )
def published_posts_overview() -> list[dict[str, Any]]:
    """Overview dict for each published post with fallback for category."""
    return list(
        Post.objects.filter(status=Post.Status.PUBLISHED).values(
            "title",
            author_email=F("author__email"),
            category_name=Coalesce("category__name", Value(UNCATEGORIZED_LABEL)),
        )
    )

def posts_stats() -> dict[str, Any]:
    """Aggregate statistics for posts in exactly one SQL query."""
    return Post.objects.aggregate(
        total=Count("id"),
        published=Count("id", filter=Q(status=Post.Status.PUBLISHED)),
        drafts=Count("id", filter=Q(status=Post.Status.DRAFT)),
        first_post_at=Min("created_at"),
        last_post_at=Max("created_at"),
    )
def average_comments_per_post() -> float:
    """Average number of comments on published posts rounded to 2 digits."""
    result = (
        Post.objects.filter(status=Post.Status.PUBLISHED)
        .annotate(comment_count=Count("comments"))
        .aggregate(avg_comments=Avg("comment_count", default=0.0))
    )
    avg_value = result["avg_comments"]
    return round(float(avg_value), ROUND_DIGITS) if avg_value is not None else DEFAULT_AVG_COMMENTS









def categories_with_post_count() -> QuerySet[Category]:
    """Categories with total post_count, sorted by count desc, then name."""
    return Category.objects.annotate(
        post_count=Count("posts")
    ).order_by("-post_count", "name")


def categories_with_published_count() -> QuerySet[Category]:
    """Categories with published post count, preserving zero-count categories."""
    return Category.objects.annotate(
        published_count=Count("posts", filter=Q(posts__status=Post.Status.PUBLISHED))
    )


def top_authors() -> QuerySet[User]:
    """Top 5 users by published posts count."""
    return User.objects.annotate(
        published_count=Count("posts", filter=Q(posts__status=Post.Status.PUBLISHED))
    ).order_by("-published_count")[:TOP_AUTHORS_LIMIT]


def popular_tags(min_posts: int) -> QuerySet[Tag]:
    """Tags used in at least min_posts posts."""
    return Tag.objects.annotate(
        post_count=Count("posts")
    ).filter(post_count__gte=min_posts)


def posts_per_status() -> list[dict[str, Any]]:
    """Number of posts grouped by status."""
    return list(
        Post.objects.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )


def users_activity() -> QuerySet[User]:
    """Users with distinct post and comment counts to prevent cartesian explosion."""
    return User.objects.annotate(
        post_count=Count("posts", distinct=True),
        comment_count=Count("comments", distinct=True),
    )





def search_users_by_full_name(text: str) -> QuerySet[User]:
    """Users whose full name (First Last) contains text."""
    return User.objects.annotate(
        user_full_name=Concat("first_name", Value(" "), "last_name")
    ).filter(user_full_name__icontains=text)
    
def published_posts_per_month() -> list[dict[str, Any]]:
    """Number of published posts truncated by month, oldest first."""
    return list(
        Post.objects.filter(status=Post.Status.PUBLISHED)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )
def posts_with_popularity() -> QuerySet[Post]:
    """Posts annotated with popularity label using database conditional expressions."""
    return Post.objects.annotate(
        comment_count=Count("comments")
    ).annotate(
        popularity=Case(
            When(comment_count__gte=POPULARITY_HOT_THRESHOLD, then=Value(POPULARITY_HOT)),
            When(comment_count__gte=POPULARITY_NORMAL_THRESHOLD, then=Value(POPULARITY_NORMAL)),
            default=Value(POPULARITY_QUIET),
        )
    )





def get_or_create_tag(name: str) -> tuple[Tag, bool]:
    """Retrieve or create tag safely handling slug collisions."""
    slug: str = slugify(name)
    return Tag.objects.get_or_create(slug=slug, defaults={"name": name})


def publish_old_drafts(days: int) -> int:
    """Publish drafts older than specified days in one single query."""
    cutoff = timezone.now() - timedelta(days=days)
    return Post.objects.filter(
        status=Post.Status.DRAFT,
        created_at__lt=cutoff,
    ).update(
        status=Post.Status.PUBLISHED,
        updated_at=timezone.now(),
    )


def tag_category_posts(category_slug: str, tag_slug: str) -> int:
    """Add a tag to all posts in a category without save loop."""
    tag = Tag.objects.filter(slug=tag_slug).first()
    if not tag:
        return 0
    posts = Post.objects.filter(category__slug=category_slug)
    post_count: int = posts.count()
    tag.posts.add(*posts)
    return post_count


def merge_categories(source_slug: str, target_slug: str) -> int:
    """Move all posts from source to target category and remove source."""
    target_category = Category.objects.get(slug=target_slug)
    source_category = Category.objects.get(slug=source_slug)
    moved_count: int = Post.objects.filter(category=source_category).update(
        category=target_category,
        updated_at=timezone.now(),
    )
    source_category.delete()
    return moved_count


def delete_inactive_users_comments() -> int:
    """Delete comments written by inactive users and return deleted count."""
    deleted_count, _ = Comment.objects.filter(author__is_active=False).delete()
    return deleted_count




def published_feed() -> list[str]:
    """Newest 50 published posts feed in exactly 1 SQL query."""
    posts = (
        Post.objects.filter(status=Post.Status.PUBLISHED)
        .select_related("author", "category")
        .order_by("-created_at")[:FEED_LIMIT]
    )
    lines: list[str] = []
    for post in posts:
        category_name: str = post.category.name if post.category else UNCATEGORIZED_LABEL
        lines.append(f"{post.title} | {post.author.email} | {category_name}")
    return lines
def newest_posts_with_tags() -> list[str]:
    """Newest 20 posts with comma-separated tags in at most 2 SQL queries."""
    posts = (
        Post.objects.prefetch_related("tags")
        .order_by("-created_at")[:NEWEST_TAGGED_POSTS_LIMIT]
    )
    lines: list[str] = []
    for post in posts:
        tag_names: str = ", ".join(tag.name for tag in post.tags.all())
        lines.append(f"{post.title}: {tag_names}")
    return lines
def categories_with_published_posts() -> dict[str, list[str]]:
    """Categories with titles of their published posts in at most 2 SQL queries."""
    published_posts_qs = Post.objects.filter(
        status=Post.Status.PUBLISHED
    ).order_by("-created_at")
    categories = Category.objects.prefetch_related(
        Prefetch("posts", queryset=published_posts_qs, to_attr="published_posts_list")
    )
    return {
        category.name: [post.title for post in category.published_posts_list]
        for category in categories
    }



def posts_with_last_comment() -> QuerySet[Post]:
    """Published posts annotated with the body of their newest comment."""
    newest_comment = Comment.objects.filter(
        post=OuterRef("pk")
    ).order_by("-created_at").values("body")[:1]
    return Post.objects.filter(status=Post.Status.PUBLISHED).annotate(
        last_comment=Subquery(newest_comment)
    )
def posts_with_staff_comments() -> QuerySet[Post]:
    """Posts having comments from staff members using Exists subquery."""
    staff_comments = Comment.objects.filter(
        post=OuterRef("pk"),
        author__is_staff=True,
    )
    return Post.objects.filter(Exists(staff_comments))





def users_with_draft_as_latest_post() -> QuerySet[User]:
    latest_post_status_subquery = Post.objects.filter(
        author=OuterRef("pk")
    ).order_by("-created_at").values("status")[:1]

    return User.objects.annotate(
        latest_post_status=Subquery(latest_post_status_subquery)
    ).filter(latest_post_status=Post.Status.DRAFT)


QUERIES: dict[int,Any]={
    1: categories_by_name,
    2: published_posts,
    3: newest_published_posts,
    4: post_by_slug,
    5: active_users_count,
    6: has_drafts,
    7: published_posts_page,
    8: posts_with_word_in_title,
    9: users_with_email_domain,
    10: posts_without_category,
    11: categories_by_slugs,
    12: posts_in_month,
    13:posts_last_days,
    14: posts_between,
    15: author_published_posts,
    16: posts_with_tag,
    17: comments_in_category,
    18: users_with_published_posts,
    19: posts_without_tags,
    20: users_without_comments,
    21: posts_with_both_tags,
    22: search_posts,
    23: published_posts_missing_info,
    24: edited_posts,
    25: comments_by_post_author,
    26: comments_before_post,
    27: published_authors_emails,
    28: published_posts_overview,
    29: posts_stats,
    30: average_comments_per_post,
    31: categories_with_post_count,
    32: categories_with_published_count,
    33: top_authors,
    34: popular_tags,
    35: posts_per_status,
    36: users_activity,
    37: search_users_by_full_name,
    38: published_posts_per_month,
    39: posts_with_popularity,
    40: get_or_create_tag,
    41: publish_old_drafts,
    42: tag_category_posts,
    43: merge_categories,
    44: delete_inactive_users_comments,
    45: published_feed,
    46: newest_posts_with_tags,
    47: categories_with_published_posts,
    48: posts_with_last_comment,
    49: posts_with_staff_comments,
    50: users_with_draft_as_latest_post,
}
