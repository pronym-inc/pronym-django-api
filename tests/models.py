from django.db import models

from pronym_api.models.owned_model import OwnedModel


class UserAccount(models.Model):
    name = models.CharField(max_length=255, null=True)
    profile = models.OneToOneField(
        'UserProfile',
        related_name='account',
        on_delete=models.CASCADE)
    organization = models.ForeignKey(
        'Organization',
        related_name='accounts',
        on_delete=models.CASCADE)
    categories = models.ManyToManyField(
        'Category',
        related_name='+')


class UserProfile(models.Model):
    email = models.EmailField()


class Category(models.Model):
    name = models.CharField(max_length=255)


class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)


class LogEntry(models.Model):
    account = models.ForeignKey(
        'UserAccount',
        related_name='log_entries',
        on_delete=models.CASCADE
    )
    description = models.CharField(max_length=255)


class AccountUpdate(OwnedModel):
    """An example owned model."""
    name = models.CharField(max_length=255)
