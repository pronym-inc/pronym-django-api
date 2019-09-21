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
        related_name='+',
        on_delete=models.CASCADE)
    request_method = models.CharField(max_length=255)
    request_headers = models.TextField()
    request_payload = models.TextField()
    response_payload = models.TextField()
    status_code = models.PositiveIntegerField()

    def __str__(self):
        return "[{0}] {1} {2} -> {3}".format(
            self.datetime_added,
            self.request_method,
            self.path,
            self.status_code)
