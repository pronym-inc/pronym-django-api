from django.db import models
from django.utils.timezone import now


class LogEntry(models.Model):
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
        on_delete=models.SET_NULL)
    api_account = models.ForeignKey(
        'ApiAccount',
        null=True,
        related_name='log_entries',
        on_delete=models.SET_NULL
    )
    request_method = models.CharField(max_length=255)
    request_headers = models.TextField()
    request_payload = models.TextField()
    response_payload = models.TextField()
    status_code = models.PositiveIntegerField()

    class Meta:
        indexes = [
            models.Index(fields=['api_account', 'datetime_added'])
        ]

    def __str__(self):  # pragma: no cover
        return "[{0}] {1} {2} -> {3}".format(
            self.datetime_added,
            self.request_method,
            self.path,
            self.status_code)
