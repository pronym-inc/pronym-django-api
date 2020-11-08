from django.db import models


class ApiPermission(models.Model):
    """A permission for the API."""
    name = models.CharField(max_length=255, unique=True)

    def __str__(self) -> str:
        return self.name
