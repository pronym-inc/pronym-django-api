"""A collection of asynchronous celery tasks that are useful for managing the API."""
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils.timezone import now


@shared_task
def clear_expired_tokens():
    """Clear out all expired tokens. Should be run on a schedule."""
    from pronym_api.models import TokenWhitelistEntry
    TokenWhitelistEntry.objects.clear_expired_tokens()


@shared_task
def prune_logs():
    """Use this task to prune logs occasionally, based on datetime"""
    if settings.PRONYM_DJANGO_API_LOG_LIFETIME_IN_DAYS is None:
        return
    from pronym_api.models import LogEntry
    cutoff = now() - timedelta(days=settings.PRONYM_DJANGO_API_LOG_LIFETIME_IN_DAYS)
    LogEntry.objects.filter(datetime_added__lt=cutoff).delete()
