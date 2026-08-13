from django.core.cache import cache
from django.db import IntegrityError, transaction

from .models import BookSummary
from .services import AISummaryService


class SummaryManager:
    """Coordinates persisted generation state, cache reads, and AI calls."""

    CACHE_TIMEOUT = 86400

    @classmethod
    def _claim_generation(cls, book, summary_type):
        """Commit PROCESSING before the slow external request begins."""
        try:
            with transaction.atomic():
                summary, created = BookSummary.objects.select_for_update().get_or_create(
                    book=book,
                    summary_type=summary_type,
                    defaults={"status": BookSummary.Status.PROCESSING},
                )

                if created:
                    return summary, True

                if summary.status == BookSummary.Status.COMPLETED:
                    return summary, False

                if summary.status == BookSummary.Status.PROCESSING:
                    return summary, False

                # Retry a previously failed generation.
                summary.status = BookSummary.Status.PROCESSING
                summary.save(update_fields=["status", "updated_at"])
                return summary, True
        except IntegrityError:
            # Another request created the unique (book, type) row first.
            # Once that transaction commits, expose its PROCESSING state.
            summary = BookSummary.objects.get(book=book, summary_type=summary_type)
            return summary, False

    @classmethod
    def get_or_generate(cls, book, summary_type):
        cache_key = f"summary:{book.id}:{summary_type}"
        cached_summary = cache.get(cache_key)
        if cached_summary:
            return {"status": "COMPLETED", "cached": True, "summary": cached_summary}

        summary_obj, claimed = cls._claim_generation(book, summary_type)

        if not claimed:
            if summary_obj.status == BookSummary.Status.COMPLETED:
                cache.set(cache_key, summary_obj.summary, timeout=cls.CACHE_TIMEOUT)
                return {"status": "COMPLETED", "cached": True, "summary": summary_obj.summary}
            return {"status": "PROCESSING", "cached": False, "summary": None}

        try:
            generated_summary = AISummaryService.generate_summary(book, summary_type)
        except Exception:
            # This uses a separate transaction, so FAILED persists even when
            # the caller receives an error response.
            with transaction.atomic():
                BookSummary.objects.filter(pk=summary_obj.pk).update(
                    status=BookSummary.Status.FAILED
                )
            raise

        with transaction.atomic():
            BookSummary.objects.filter(pk=summary_obj.pk).update(
                summary=generated_summary,
                status=BookSummary.Status.COMPLETED,
            )
        cache.set(cache_key, generated_summary, timeout=cls.CACHE_TIMEOUT)

        return {"status": "COMPLETED", "cached": False, "summary": generated_summary}
