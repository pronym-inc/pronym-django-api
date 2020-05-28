"""
Model for logging API requests.
"""

from django.db import models
from django.utils.timezone import now

from pronym_api.models.owned_model import OwnedModel


class LogEntry(OwnedModel):
    """A log record of a specific API call."""
    datetime_added = models.DateTimeField(default=now)
    endpoint_name = models.CharField(max_length=255)
    source_ip = models.CharField(max_length=255)
    path = models.CharField(max_length=255)
    host = models.CharField(max_length=255)
    port = models.PositiveIntegerField()
    is_authenticated = models.BooleanField()
    authenticated_profile = models.ForeignKey(
        'ApiAccountMember',
        null=True,
        related_name='log_entries',
        on_delete=models.CASCADE)
    request_method = models.CharField(max_length=255)
    request_headers = models.TextField()
    request_payload = models.TextField()
    response_payload = models.TextField()
    status_code = models.PositiveIntegerField()

    class Meta:
        indexes = [
            models.Index(fields=['datetime_added']),
            models.Index(fields=['authenticated_profile'])
        ]

    def __str__(self) -> str:  # pragma: no cover
        return "[{0}] {1} {2} -> {3}".format(
            self.datetime_added,
            self.request_method,
            self.path,
            self.status_code)
