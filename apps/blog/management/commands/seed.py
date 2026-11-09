# Python modules
import random
import time
from typing import Any

# Third-party modules
from faker import Faker

# Django modules
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils.text import slugify

# Project modules
from apps.auths.models import User
from apps.blog.models import Category, Comment, Post, Tag


class Command(BaseCommand):
    """Fill the database with fake data."""

    help = "Fill the database with fake data."

    DEFAULT_USERS = 20
    DEFAULT_POSTS = 100
    DEFAULT_COMMENTS = 500

    SEED_PASSWORD = "password123"

    STAFF_USER_RATIO = 0.10
    INACTIVE_USER_RATIO = 0.15

    PUBLISHED_POST_RATIO = 0.70
    NO_CATEGORY_RATIO = 0.10

    MIN_TAGS_PER_POST = 0
    MAX_TAGS_PER_POST = 5

    MIN_SENTENCES_PER_COMMENT = 1
    MAX_SENTENCES_PER_COMMENT = 3

    CATEGORIES = (
        "Python",
        "Django",
        "DevOps",
        "Frontend",
        "Backend",
        "Mobile Development",
        "Databases",
        "Machine Learning",
    )

    TAGS = (
        "python",
        "django",
        "fastapi",
        "react",
        "typescript",
        "docker",
        "kubernetes",
        "postgresql",
        "redis",
        "celery",
        "graphql",
        "rest-api",
        "testing",
        "ci-cd",
        "aws",
        "linux",
        "tailwind",
        "nextjs",
        "vue",
        "microservices",
    )

    EMAIL_DOMAINS = (
        "example.com",
        "kbtu.kz",
        "blog.kz",
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fake = Faker()

    def add_arguments(self, parser: CommandParser) -> None:
        """Add command line arguments."""
        parser.add_argument(
            "--users",
            type=int,
            default=self.DEFAULT_USERS,
            help="Number of users to create",
        )
        parser.add_argument(
            "--posts",
            type=int,
            default=self.DEFAULT_POSTS,
            help="Number of posts to create",
        )
        parser.add_argument(
            "--comments",
            type=int,
            default=self.DEFAULT_COMMENTS,
            help="Number of comments to create",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing data before seeding",
        )

    def __clear_data(self) -> None:
        """Clear existing blog data and non-superuser users."""
        Comment.objects.all().delete()
        Post.objects.all().delete()
        Tag.objects.all().delete()
        Category.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

    def __generate_users(self, count: int) -> list[User]:
        """Generate fake users with hashed password and unique email addresses."""
        if count <= 0:
            return []

        existing_emails: set[str] = set(User.objects.values_list("email", flat=True))
        users_to_create: list[User] = []
        password_hash: str = make_password(self.SEED_PASSWORD)

        created: int = 0
        attempts: int = 0
        max_attempts: int = count * 20

        while created < count and attempts < max_attempts:
            attempts += 1
            first_name: str = self.fake.first_name()
            last_name: str = self.fake.last_name()
            domain: str = random.choice(self.EMAIL_DOMAINS)

            clean_first: str = first_name.lower().replace(" ", "")
            clean_last: str = last_name.lower().replace(" ", "")
            suffix: int = random.randint(1, 9999)
            email: str = f"{clean_first}.{clean_last}{suffix}@{domain}"

            if email in existing_emails:
                continue

            existing_emails.add(email)

            is_staff: bool = random.random() < self.STAFF_USER_RATIO
            is_active: bool = random.random() >= self.INACTIVE_USER_RATIO
            if is_staff:
                is_active = True

            users_to_create.append(
                User(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password_hash,
                    is_staff=is_staff,
                    is_active=is_active,
                )
            )
            created += 1

        User.objects.bulk_create(users_to_create)
        return users_to_create

    def __generate_categories(self) -> tuple[list[Category], int]:
        """Generate predefined categories, skipping existing ones."""
        existing_slugs: set[str] = set(Category.objects.values_list("slug", flat=True))
        categories_to_create: list[Category] = []

        for name in self.CATEGORIES:
            slug: str = slugify(name)
            if slug not in existing_slugs:
                existing_slugs.add(slug)
                categories_to_create.append(
                    Category(
                        name=name,
                        slug=slug,
                    )
                )

        if categories_to_create:
            Category.objects.bulk_create(categories_to_create)

        all_categories: list[Category] = list(Category.objects.all())
        return all_categories, len(categories_to_create)

    def __generate_tags(self) -> tuple[list[Tag], int]:
        """Generate predefined tags, skipping existing ones."""
        existing_slugs: set[str] = set(Tag.objects.values_list("slug", flat=True))
        tags_to_create: list[Tag] = []

        for name in self.TAGS:
            slug: str = slugify(name)
            if slug not in existing_slugs:
                existing_slugs.add(slug)
                tags_to_create.append(
                    Tag(
                        name=name,
                        slug=slug,
                    )
                )

        if tags_to_create:
            Tag.objects.bulk_create(tags_to_create)

        all_tags: list[Tag] = list(Tag.objects.all())
        return all_tags, len(tags_to_create)

    def __generate_posts(
        self,
        count: int,
        users: list[User],
        categories: list[Category],
        tags: list[Tag],
    ) -> list[Post]:
        """Generate posts with unique slugs and random tags."""
        if count <= 0:
            return []

        existing_slugs: set[str] = set(Post.objects.values_list("slug", flat=True))
        posts_to_create: list[Post] = []
        post_tags_map: list[list[Tag]] = []

        for i in range(count):
            author: User = random.choice(users)
            title: str = self.fake.sentence(nb_words=random.randint(4, 8)).rstrip(".")
            base_slug: str = slugify(title)
            if not base_slug:
                base_slug = f"post-{random.randint(1000, 999999)}"

            slug: str = base_slug
            suffix: int = 2
            while slug in existing_slugs:
                slug = f"{base_slug}-{suffix}"
                suffix += 1
            existing_slugs.add(slug)

            body: str = "\n\n".join(self.fake.paragraphs(nb=random.randint(3, 5)))

            if categories and random.random() >= self.NO_CATEGORY_RATIO:
                category: Category | None = random.choice(categories)
            else:
                category = None

            # ~70% published, 30% draft
            is_published: bool = i < int(count * self.PUBLISHED_POST_RATIO) or (
                random.random() < self.PUBLISHED_POST_RATIO
            )
            status: str = Post.Status.PUBLISHED if is_published else Post.Status.DRAFT

            posts_to_create.append(
                Post(
                    title=title,
                    slug=slug,
                    body=body,
                    author=author,
                    category=category,
                    status=status,
                )
            )

            # Determine 0-5 random tags for this post
            if tags:
                tag_count: int = random.randint(self.MIN_TAGS_PER_POST, min(self.MAX_TAGS_PER_POST, len(tags)))
                selected_tags: list[Tag] = random.sample(tags, k=tag_count)
            else:
                selected_tags = []
            post_tags_map.append(selected_tags)

        created_posts: list[Post] = Post.objects.bulk_create(posts_to_create)

        # Attach tags using through table in bulk for efficiency and database independence
        through_records: list[Any] = []
        through_model = Post.tags.through
        for post, assigned_tags in zip(created_posts, post_tags_map):
            for tag in assigned_tags:
                through_records.append(
                    through_model(
                        post_id=post.id,
                        tag_id=tag.id,
                    )
                )

        if through_records:
            through_model.objects.bulk_create(through_records)

        return created_posts

    def __generate_comments(
        self,
        count: int,
        users: list[User],
        published_posts: list[Post],
    ) -> list[Comment]:
        """Generate comments for published posts only."""
        if count <= 0 or not published_posts or not users:
            return []

        comments_to_create: list[Comment] = []
        for _ in range(count):
            post: Post = random.choice(published_posts)
            author: User = random.choice(users)
            sentence_count: int = random.randint(
                self.MIN_SENTENCES_PER_COMMENT,
                self.MAX_SENTENCES_PER_COMMENT,
            )
            body: str = self.fake.paragraph(nb_sentences=sentence_count)

            comments_to_create.append(
                Comment(
                    post=post,
                    author=author,
                    body=body,
                )
            )

        Comment.objects.bulk_create(comments_to_create)
        return comments_to_create

    def handle(self, *args: tuple[Any, ...], **options: dict[str, Any]) -> None:
        """Command entry point."""
        start_time: float = time.perf_counter()

        users_count: int = options["users"]
        posts_count: int = options["posts"]
        comments_count: int = options["comments"]
        clear: bool = options["clear"]

        # Validate arguments
        if users_count < 0:
            raise CommandError("Number of users cannot be negative.")
        if posts_count < 0:
            raise CommandError("Number of posts cannot be negative.")
        if comments_count < 0:
            raise CommandError("Number of comments cannot be negative.")

        if clear:
            self.__clear_data()

        # Check user availability
        current_users_count: int = User.objects.count()
        if (posts_count > 0 or comments_count > 0) and (current_users_count + users_count == 0):
            raise CommandError("Cannot create posts or comments without users.")

        # 1. Create Users
        created_users: list[User] = self.__generate_users(users_count)
        all_users: list[User] = list(User.objects.all())

        # 2. Create Categories & Tags
        all_categories, created_categories_cnt = self.__generate_categories()
        all_tags, created_tags_cnt = self.__generate_tags()

        # 3. Create Posts
        created_posts: list[Post] = self.__generate_posts(
            count=posts_count,
            users=all_users,
            categories=all_categories,
            tags=all_tags,
        )

        # 4. Check published posts for comments
        existing_published_posts: list[Post] = list(
            Post.objects.filter(status=Post.Status.PUBLISHED)
        )
        if comments_count > 0 and not existing_published_posts:
            raise CommandError("Cannot create comments without published posts.")

        # 5. Create Comments
        created_comments: list[Comment] = self.__generate_comments(
            count=comments_count,
            users=all_users,
            published_posts=existing_published_posts,
        )

        elapsed: float = time.perf_counter() - start_time

        self.stdout.write(f"Users:      {len(created_users):>5} created")
        self.stdout.write(f"Categories: {created_categories_cnt:>5} created")
        self.stdout.write(f"Tags:       {created_tags_cnt:>5} created")
        self.stdout.write(f"Posts:      {len(created_posts):>5} created")
        self.stdout.write(f"Comments:   {len(created_comments):>5} created")
        self.stdout.write(self.style.SUCCESS(f"Done in {elapsed:.2f} seconds"))
