"""A collection of asynchronous celery tasks that are useful for managing the API."""
from celery import shared_task


@shared_task
def clear_expired_tokens():
    """Clear out all expired tokens. Should be run on a schedule."""
    from pronym_api.models import TokenWhitelistEntry
    TokenWhitelistEntry.objects.clear_expired_tokens()
