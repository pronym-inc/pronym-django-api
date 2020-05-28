"""
Logic for handling authentication using the JWT protocol:

https://jwt.io/introduction/
"""

import random

from datetime import timedelta, datetime
from typing import TYPE_CHECKING, Optional, cast, Dict, Any

from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.timezone import now

import jwt
from jwt import InvalidTokenError

if TYPE_CHECKING:  # pragma: no cover
    from pronym_api.models.api_account import ApiAccount
    from pronym_api.models.api_account_member import ApiAccountMember


class TokenWhitelistEntryManager(models.Manager):
    """
    Custom manager to handle expired tokens and generating tokens for users.
    """
    def clear_expired_tokens(self) -> None:
        """
        Delete all expired tokens.
        """
        expiration_cutoff = self.model.get_expiration_cutoff()
        self.filter(datetime_added__lt=expiration_cutoff).delete()

    def clear_tokens_for_account(self, account: 'ApiAccount') -> None:
        """
        Delete all the tokens for an account.
        :param account: The account to clear tokens for
        """
        TokenWhitelistEntry.objects.filter(api_account_member__api_account=account).delete()

    def clear_tokens_for_account_member(self, account_member: 'ApiAccountMember') -> None:
        """
        Delete all the tokens for an API account member.
        :param account_member: The account member to clear tokens for.
        """
        TokenWhitelistEntry.objects.filter(api_account_member=account_member).delete()

    def create_for_account_member(self, account_member: 'ApiAccountMember') -> 'TokenWhitelistEntry':
        """
        Create a new token for an account member.
        :param account_member: The ApiAccountMember
        :return: A TokenWhitelistEntry object with the new token.
        """
        return TokenWhitelistEntry.objects.create(api_account_member=account_member)

    def get_account_member_for_token(self, token: str) -> 'Optional[ApiAccountMember]':
        """
        :param token:
        :return:
        """
        try:
            payload = jwt.decode(
                token,
                settings.API_SECRET,
                algorithms=['HS256'],
                audience=settings.JWT_AUD,
                issuer=settings.JWT_ISS)
        except InvalidTokenError:
            return None
        entry_id = payload['jti']
        try:
            entry = self.get(token_entropy=entry_id)
        except self.model.DoesNotExist:
            return None
        if not entry.validate(payload):
            return None
        return entry.api_account_member


class TokenWhitelistEntry(models.Model):
    """
    Basically this represents a token that can be used to authenticate.  The token they send will be destructured
    into values that can be used to look up rows in this table.
    """
    datetime_added = models.DateTimeField(default=now)
    token_entropy = models.PositiveIntegerField(null=True, unique=True)
    api_account_member = models.ForeignKey(
        'ApiAccountMember',
        related_name='token_whitelist_entries',
        on_delete=models.CASCADE)

    objects = TokenWhitelistEntryManager()

    class Meta:
        indexes = [
            models.Index(fields=["token_entropy"])
        ]

    @staticmethod
    def get_expiration_cutoff() -> datetime:
        """
        :return: The datetime cutoff for expired tokens.
        """
        expiration_window = timedelta(minutes=settings.TOKEN_EXPIRATION_MINUTES)
        expiration_cutoff = now() - expiration_window
        return expiration_cutoff

    def encode(self) -> str:
        """
        :return: A string serialization of the authentication payload - this will result in the token that the user
        will need to use to authenticate.
        """
        data = {
            'exp': self.get_expiration_date().timestamp(),
            'iat': cast(datetime, self.datetime_added).timestamp(),
            'jti': self.token_entropy,
            'sub': settings.JWT_SUB,
            'aud': settings.JWT_AUD,
            'nbf': cast(datetime, self.datetime_added).timestamp(),
            'iss': settings.JWT_ISS
        }
        return jwt.encode(
            data,
            settings.API_SECRET,
            algorithm='HS256'
        ).decode('ascii')

    def get_expiration_date(self) -> datetime:
        """
        :return: The datetime when this token expires.
        """
        return cast(datetime, self.datetime_added) + timedelta(minutes=settings.TOKEN_EXPIRATION_MINUTES)

    def is_expired(self) -> bool:
        """
        :return: bool, whether or not this token is expired.
        """
        return self.datetime_added < self.get_expiration_cutoff()

    def validate(self, payload: Dict[str, str]) -> bool:
        """
        :param payload: The deserialized/decrypted payload of a token
        :return: Whether or not the given payload is valid (not expired and valid form/contents)
        """
        if self.is_expired():
            return False
        if cast(datetime, self.datetime_added).timestamp() != float(payload['iat']):
            return False
        if cast(datetime, self.datetime_added).timestamp() != float(payload['nbf']):
            return False
        if payload['sub'] != settings.JWT_SUB:
            return False
        return True


@receiver(pre_save, sender=TokenWhitelistEntry)
def pre_save_token(sender, instance, **_: Any):
    """
    Pre-save hook to generate an entropy value for the new token.
    """
    if instance.token_entropy is None:
        # Generate a unique int.
        while True:
            candidate = random.randint(1, 500000000)
            try:
                sender.objects.get(token_entropy=candidate)
            except sender.DoesNotExist:
                break
        instance.token_entropy = candidate
