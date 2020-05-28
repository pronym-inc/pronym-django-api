"""
An individual user for an api account.  Authentication is done at the member level, so this model will control
    access for specific users.
"""
from django.db import models

from pronym_api.models.owned_model import OwnedModel
from pronym_api.models.token_whitelist_entry import TokenWhitelistEntry


class ApiAccountMember(OwnedModel):
    """
    An individual user for an api account.  Authentication is done at the member level, so this model will control
    access for specific users.
    """
    USERNAME_LENGTH = 15
    PASSWORD_LENGTH = 15

    user = models.ForeignKey(
        'auth.User',
        related_name='api_members',
        on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=['api_account']),
            models.Index(fields=['user'])
        ]

    def __str__(self) -> str:  # pragma: no cover
        return "{0} ({1})".format(
            self.user.username,
            self.api_account.name)

    def create_whitelist_entry(self) -> TokenWhitelistEntry:
        """
        Create a new whitelist entry, and therefore token, for the user.
        :return: The TokenWhitelistEntry object.
        """
        return TokenWhitelistEntry.objects.create_for_account_member(self)
