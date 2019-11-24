from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from pronym_api.test_utils.factories import ApiAccountFactory


class ApiAccountTestCase(TestCase):
    def setUp(self):
        self.account = ApiAccountFactory()

    def test___str__(self):
        self.assertEqual(str(self.account), self.account.name)

    @patch.object(User.objects, 'make_random_password')
    def test_create_account_member(self, _mrp):
        _mrp.side_effect = ["fakeusername", "fakeusername", "fakeusername2"]
        account_member = self.account.create_account_member()
        self.assertEqual(account_member.user.username, "fakeusername")
        self.assertEqual(account_member.api_account, self.account)
        # We will use the same mock value twice to simulate
        # the very rare occurrence that the same username
        # is generated twice.
        account_member2 = self.account.create_account_member()
        self.assertEqual(account_member2.user.username, "fakeusername2")
        self.assertEqual(account_member2.api_account, self.account)

    def test_get_active_member(self):
        self.assertIsNone(self.account.get_active_member())
        account_member = self.account.create_account_member()
        self.assertEqual(self.account.get_active_member(), account_member)

    def test_regenerate_secret_key(self):
        # Running it now should create a member
        self.account.regenerate_secret_key()
        member = self.account.get_active_member()
        self.assertIsNotNone(member)
        old_password = member.user.password
        # Running it again should change our password
        self.account.regenerate_secret_key()
        member = self.account.get_active_member()
        self.assertNotEqual(old_password, member.user.password)

    def test_has_active_member(self):
        self.assertFalse(self.account.has_active_member)
        self.account.create_account_member()
        self.assertTrue(self.account.has_active_member)
