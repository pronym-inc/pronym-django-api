from django.db import models


class UserAccount(models.Model):
    name = models.CharField(max_length=255, null=True)
    profile = models.OneToOneField(
        'UserProfile',
        related_name='account',
        on_delete=models.CASCADE,
        editable=False)
    organization = models.ForeignKey(
        'Organization',
        related_name='accounts',
        on_delete=models.CASCADE,
        editable=False)
    categories = models.ManyToManyField(
        'Category',
        related_name='+',
        editable=False)


class UserProfile(models.Model):
    email = models.EmailField()


class UserLogEntry(models.Model):
    user = models.ForeignKey(
        'UserAccount',
        on_delete=models.CASCADE,
        related_name='log_entries',
        editable=False)
    name = models.CharField(max_length=255)


class Category(models.Model):
    name = models.CharField(max_length=255)


class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
