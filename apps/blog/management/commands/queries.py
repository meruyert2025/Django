"""Management command to benchmark and execute ORM queries."""
from datetime import timedelta
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.models import Model, QuerySet
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.blog.models import Category, Post, Tag
from apps.blog.queries import QUERIES


class Command(BaseCommand):

    help = "Run and inspect ORM queries from apps.blog.queries"

    PREVIEW_LIMIT: int = 5
    DATA_MODIFYING_QUERIES: set[int] = {40, 41, 42, 43, 44}

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--number",
            type=int,
            help="Run a specific query by its number (1-50)",
        )
        parser.add_argument(
            "--sql",
            action="store_true",
            help="Print captured SQL queries executed during the call",
        )

    def _get_query_arguments(self) -> dict[int, dict[str, Any]]:
        sample_post = Post.objects.filter(status=Post.Status.PUBLISHED).first()
        post_slug = sample_post.slug if sample_post else "post-1"
        author_email = sample_post.author.email if sample_post else "admin@kbtu.kz"

        sample_tag = Tag.objects.first()
        tag_slug = sample_tag.slug if sample_tag else "python"

        second_tag = Tag.objects.last()
        second_tag_slug = second_tag.slug if second_tag else "django"

        sample_cat = Category.objects.first()
        cat_slug = sample_cat.slug if sample_cat else "backend"

        last_cat = Category.objects.last()
        target_cat_slug = last_cat.slug if last_cat else "devops"

        now = timezone.now()

        return {
            4: {"slug": post_slug},
            7: {"page": 1},
            8: {"word": "a"},
            9: {"domain": author_email.split("@")[-1] if "@" in author_email else "kbtu.kz"},
            11: {"slugs": list(Category.objects.values_list("slug", flat=True)[:3])},
            12: {"year": now.year, "month": now.month},
            13: {"days": 365},
            14: {"start": (now - timedelta(days=365)).date(), "end": now.date()},
            15: {"email": author_email},
            16: {"tag_slug": tag_slug},
            17: {"category_slug": cat_slug},
            21: {"first_slug": tag_slug, "second_slug": second_tag_slug},
            22: {"text": "a"},
            34: {"min_posts": 1},
            37: {"text": "a"},
            40: {"name": "Docker"},
            41: {"days": 30},
            42: {"category_slug": cat_slug, "tag_slug": tag_slug},
            43: {"source_slug": cat_slug, "target_slug": target_cat_slug},
        }

    def _format_row(self, item: Any, queryset: QuerySet | None = None) -> str:
        if isinstance(item, Model):
            annotations = {}
            if queryset is not None and hasattr(queryset, "query"):
                for key in queryset.query.annotations.keys():
                    if hasattr(item, key):
                        annotations[key] = getattr(item, key)
            if annotations:
                return f"{item} {annotations}"
            return str(item)
        return str(item)

    def _execute_query(self, number: int, show_sql: bool, sample_args: dict[int, dict[str, Any]]) -> None:
        func = QUERIES[number]
        kwargs = sample_args.get(number, {})

        with CaptureQueriesContext(connection) as context:
            result = func(**kwargs)
            evaluated_rows = None
            if isinstance(result, QuerySet):
                evaluated_rows = list(result)

        query_count: int = len(context.captured_queries)
        unit: str = "SQL query" if query_count == 1 else "SQL queries"
        self.stdout.write(f"#{number} {func.__name__} — {query_count} {unit}")

        if show_sql:
            for q in context.captured_queries:
                self.stdout.write(self.style.SQL_KEYWORD(q["sql"]))

        if evaluated_rows is not None:
            for row in evaluated_rows[: self.PREVIEW_LIMIT]:
                self.stdout.write(f"  {self._format_row(row, result)}")
            self.stdout.write(f"  ({len(evaluated_rows)} rows)")
        elif isinstance(result, list):
            for row in result[: self.PREVIEW_LIMIT]:
                self.stdout.write(f"  {row}")
            self.stdout.write(f"  ({len(result)} rows)")
        elif isinstance(result, dict):
            if result and all(isinstance(v, list) for v in result.values()):
                items = list(result.items())
                for k, v in items[: self.PREVIEW_LIMIT]:
                    self.stdout.write(f"  {k}: {v[:3]} (total {len(v)} posts)")
                self.stdout.write(f"  ({len(result)} rows)")
            else:
                self.stdout.write(f"  {result}")
        else:
            self.stdout.write(f"  {result}")

    def handle(self, *args: tuple[Any, ...], **options: dict[str, Any]) -> None:
        number: int | None = options["number"]
        show_sql: bool = options["sql"]

        sample_args = self._get_query_arguments()

        if number is not None:
            if number not in QUERIES:
                raise CommandError(f"Query #{number} does not exist (valid range: 1-50).")
            self._execute_query(number, show_sql, sample_args)
            return

        for num in sorted(QUERIES.keys()):
            if num in self.DATA_MODIFYING_QUERIES:
                continue
            self._execute_query(num, show_sql, sample_args)