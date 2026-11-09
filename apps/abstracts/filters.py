# Django modules
from django.contrib.admin import SimpleListFilter
from django.db.models import QuerySet
from django.http import HttpRequest


class IsDeletedListFilter(SimpleListFilter):
    """Filter for soft deleted objects."""

    title = "Is deleted object"
    parameter_name = "is_deleted"

    DELETED_KEY = "deleted"
    NONDELETED_KEY = "non-deleted"

    def lookups(self, request: HttpRequest, model_admin: object) -> list[tuple[str, str]]:
        """Options: (value in the URL, text for people)."""
        return [
            (self.DELETED_KEY, "Deleted"),
            (self.NONDELETED_KEY, "Not deleted"),
        ]

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        """Filter the rows by the chosen option."""
        if self.value() == self.DELETED_KEY:
            return queryset.filter(deleted_at__isnull=False)
        if self.value() == self.NONDELETED_KEY:
            return queryset.filter(deleted_at__isnull=True)
        return queryset.all()
