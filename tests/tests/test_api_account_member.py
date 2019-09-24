from django.test import TestCase

from tests.factories import ApiAccountMemberFactory


class ApiAccountMemberTestCase(TestCase):
    def setUp(self):
        self.member = ApiAccountMemberFactory()

    def test_create_whitelist_entry(self):
        self.member.create_whitelist_entry()
        self.assertEqual(self.member.token_whitelist_entries.count(), 1)
