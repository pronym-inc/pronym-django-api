import pytz

from datetime import datetime, timedelta
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase

import jwt

from pronym_api.models import TokenWhitelistEntry
from pronym_api.test_utils.factories import (
    ApiAccountFactory, ApiAccountMemberFactory, TokenWhitelistEntryFactory)


def fake_now():
    return pytz.UTC.localize(datetime(2019, 1, 1))


@patch('pronym_api.models.token_whitelist_entry.now', fake_now)
class TokenWhitelistEntryManagerTestCase(TestCase):
    def test_clear_expired_tokens(self):
        expired_dt = (
            fake_now() -
            timedelta(minutes=settings.TOKEN_EXPIRATION_MINUTES + 1))
        t1 = TokenWhitelistEntryFactory(datetime_added=expired_dt)
        t2 = TokenWhitelistEntryFactory(datetime_added=fake_now())
        TokenWhitelistEntry.objects.clear_expired_tokens()

        self.assertEqual(
            TokenWhitelistEntry.objects.filter(id=t1.id).count(),
            0
        )
        self.assertEqual(
            TokenWhitelistEntry.objects.filter(id=t2.id).count(),
            1
        )

    def test_clear_tokens_for_account(self):
        account1 = ApiAccountFactory()
        account2 = ApiAccountFactory()
        for _ in range(3):
            TokenWhitelistEntryFactory(
                api_account_member__api_account=account1)
        for _ in range(2):
            TokenWhitelistEntryFactory(
                api_account_member__api_account=account2)
        TokenWhitelistEntry.objects.clear_tokens_for_account(account1)

        self.assertEqual(
            TokenWhitelistEntry.objects.filter(
                api_account_member__api_account=account1).count(),
            0)

        self.assertEqual(
            TokenWhitelistEntry.objects.filter(
                api_account_member__api_account=account2).count(),
            2)

    def test_clear_tokens_for_account_member(self):
        account1 = ApiAccountFactory()
        member1 = ApiAccountMemberFactory(api_account=account1)
        member2 = ApiAccountMemberFactory(api_account=account1)

        account2 = ApiAccountFactory()
        member3 = ApiAccountMemberFactory(api_account=account2)

        for member in (member1, member2, member3):
            for _ in range(3):
                TokenWhitelistEntryFactory(api_account_member=member)

        TokenWhitelistEntry.objects.clear_tokens_for_account_member(member1)

        self.assertEqual(member1.token_whitelist_entries.count(), 0)
        self.assertEqual(member2.token_whitelist_entries.count(), 3)
        self.assertEqual(member3.token_whitelist_entries.count(), 3)

    def test_get_account_member_for_token(self):
        member = ApiAccountMemberFactory()
        entry = TokenWhitelistEntryFactory(api_account_member=member)
        token = entry.encode()
        # Should get our user back.
        found_member = TokenWhitelistEntry.objects\
            .get_account_member_for_token(token)
        self.assertEqual(member, found_member)
        # Now we mess with the token and it should fail.
        decoded_token = jwt.decode(
            token,
            settings.API_SECRET,
            algorithms=['HS256'],
            audience=settings.JWT_AUD,
            issuer=settings.JWT_ISS)
        decoded_token['iss'] = 'nonsense'
        reencoded_token = jwt.encode(
            decoded_token, settings.API_SECRET, algorithm='HS256').decode(
            'ascii')
        self.assertIsNone(
            TokenWhitelistEntry.objects.get_account_member_for_token(
                reencoded_token))

        decoded_token = jwt.decode(
            token,
            settings.API_SECRET,
            algorithms=['HS256'],
            audience=settings.JWT_AUD,
            issuer=settings.JWT_ISS)
        decoded_token['jti'] = -1
        reencoded_token = jwt.encode(
            decoded_token, settings.API_SECRET, algorithm='HS256').decode(
            'ascii')
        self.assertIsNone(
            TokenWhitelistEntry.objects.get_account_member_for_token(
                reencoded_token))

        decoded_token = jwt.decode(
            token,
            settings.API_SECRET,
            algorithms=['HS256'],
            audience=settings.JWT_AUD,
            issuer=settings.JWT_ISS)
        decoded_token['sub'] = "mew"
        reencoded_token = jwt.encode(
            decoded_token, settings.API_SECRET, algorithm='HS256').decode(
            'ascii')
        self.assertIsNone(
            TokenWhitelistEntry.objects.get_account_member_for_token(
                reencoded_token))
