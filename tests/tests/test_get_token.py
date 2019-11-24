from json import loads

from pronym_api.api.get_token import GetTokenApiView
from pronym_api.test_utils.api_testcase import PronymApiTestCase
from tests.test_views.authenticated_sample import (
    AuthenticatedSampleApiView)
from pronym_api.test_utils.factories import ApiAccountMemberFactory


class GetTokenTest(PronymApiTestCase):
    view_class = GetTokenApiView

    def get_valid_data(self, **data):
        data.setdefault('username', self.account_member.user.username)
        data.setdefault('password', self.my_password)
        return PronymApiTestCase.get_valid_data(self, **data)

    def setUp(self):
        PronymApiTestCase.setUp(self)
        self.my_password = 'passwordius'
        self.account_member = ApiAccountMemberFactory(
            user__password=self.my_password)

    def test_invalid_data(self):
        response = self.post(data={})
        self.assertEqual(response.status_code, 400)

    def test_invalid_username(self):
        response = self.post(username="bob")
        self.assertEqual(response.status_code, 400)

    def test_invalid_password(self):
        response = self.post(password="mu")
        self.assertEqual(response.status_code, 400)

    def test_login(self):
        response = self.post()
        self.assertEqual(response.status_code, 200)
        response_data = loads(response.content)
        self.assertIn("token", response_data)
        self.assertIn("expires", response_data)
        # Token should allow access to an authenticated endpoint
        response = self.get(
            data={'name': 'yo'},
            view=AuthenticatedSampleApiView.as_view(),
            auth_token=response_data['token'],
            use_authentication=True)
        self.assertEqual(response.status_code, 200)
