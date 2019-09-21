import random

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.timezone import now

import jwt


class TokenWhitelistEntryManager(models.Manager):
    def clear_expired_tokens(self):
        expiration_cutoff = self.model.get_expiration_cutoff()
        self.filter(datetime_added__lt=expiration_cutoff).delete()

    def clear_tokens_for_account(self, account):
        TokenWhitelistEntry.objects.filter(
            api_account_member__api_account=account).delete()

    def clear_tokens_for_account_member(self, account_member):
        TokenWhitelistEntry.objects.filter(
            api_account_member=account_member).delete()

    def create_for_account_member(self, account_member):
        entry = TokenWhitelistEntry.objects.create(
            api_account_member=account_member)
        return entry

    def get_account_member_for_token(self, token):
        payload = jwt.decode(
            token,
            settings.API_SECRET,
            algorithms=['HS256'],
            audience="bridgenet",
            issuer="bridgenetapi")
        entry_id = payload['jti']
        try:
            entry = self.get(id=entry_id)
        except self.model.DoesNotExist:
            return None
        if not entry.validate(payload):
            return None
        return entry.api_account_member


class TokenWhitelistEntry(models.Model):
    datetime_added = models.DateTimeField(default=now)
    token_entropy = models.PositiveIntegerField(null=True)
    api_account_member = models.ForeignKey(
        'ApiAccountMember',
        related_name='p_token_whitelist_entries',
        on_delete=models.CASCADE)

    objects = TokenWhitelistEntryManager()

    @staticmethod
    def get_expiration_cutoff():
        expiration_window = timedelta(
            minutes=settings.TOKEN_EXPIRATION_MINUTES)
        expiration_cutoff = now() - expiration_window
        return expiration_cutoff

    def encode(self):
        data = {
            'exp': self.get_expiration_date().timestamp(),
            'iat': self.datetime_added.timestamp(),
            'jti': self.token_entropy,
            'sub': 'bridgenet',
            'aud': 'bridgenet',
            'nbf': self.datetime_added.timestamp(),
            'iss': 'bridgenetapi'
        }
        return jwt.encode(
            data,
            settings.API_SECRET,
            algorithm='HS256').decode('ascii')

    def get_expiration_date(self):
        return self.datetime_added + timedelta(
            minutes=settings.TOKEN_EXPIRATION_MINUTES)

    def is_expired(self):
        return self.datetime_added < self.get_expiration_cutoff()

    def validate(self, payload):
        if self.is_expired():
            return False
        if int(payload['jti']) != self.token_entropy:
            return False
        if self.datetime_added.timestamp() != float(payload['iat']):
            return False
        if self.datetime_added.timestamp() != float(payload['nbf']):
            return False
        if self.get_expiration_date().timestamp() != float(payload['exp']):
            return False
        if payload['sub'] != 'bridgenet':
            return False
        if payload['iss'] != 'bridgenetapi':
            return False
        return True


@receiver(pre_save, sender=TokenWhitelistEntry)
def pre_save_token(sender, instance, **kwargs):
    if instance.token_entropy is None:
        # Generate a unique int.
        while True:
            candidate = random.randint(1, 100000000)
            try:
                sender.objects.get(token_entry=candidate)
            except sender.DoesNotExist:
                break
        instance.token_entropy = candidate
