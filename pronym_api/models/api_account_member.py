from django.db import models

from .token_whitelist_entry import TokenWhitelistEntry


class ApiAccountMember(models.Model):
    USERNAME_LENGTH = 15
    PASSWORD_LENGTH = 15

    api_account = models.ForeignKey(
        'ApiAccount',
        related_name='p_members',
        on_delete=models.CASCADE)
    user = models.ForeignKey(
        'auth.User',
        related_name='p_api_members',
        on_delete=models.CASCADE)

    def __str__(self):
        return "{0} ({1})".format(
            self.user.username,
            self.api_account.name)

    def create_whitelist_entry(self):
        return TokenWhitelistEntry.objects.create_for_account_member(self)
