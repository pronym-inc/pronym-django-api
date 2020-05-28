"""An owned model is one that is tied to an API account.  In general, the expectation should be that
owned models will be only visible to their owners."""
from typing import TYPE_CHECKING

from django.db import models
from django.db.models import Manager, QuerySet

from pronym_api.models.api_account import ApiAccount


class OwnedModelManager(Manager):
    """Manager to access owned models."""
    def get_records_owned_by_account(self, account: 'ApiAccount') -> QuerySet:
        """Get all records owned by this account."""
        return self.all().filter(api_account=account)


class OwnedModel(models.Model):
    """An abstract class for models that are owned by an account."""
    api_account = models.ForeignKey(
        'pronym_api.ApiAccount',
        on_delete=models.CASCADE,
        null=True,
        editable=False)

    objects = OwnedModelManager()

    class Meta:
        abstract = True
