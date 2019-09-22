from pronym_api.test_utils.api_testcase import PronymApiTestCase

from tests.test_views.authenticated_sample import (
    AuthenticatedSampleApiView)
from tests.test_views.unauthenticated_sample import (
    UnauthenticatedSampleApiView)


class StatusCodeApiTest(PronymApiTestCase):
    view_class = AuthenticatedSampleApiView

    valid_data = {
        'name': 'Gregg',
        'email': 'gregg@mail.com'
    }

    def test_authenticated_should_give_200(self):
        response = self.post()
        self.assertEqual(response.status_code, 200)

    def test_invalid_json_should_give_400(self):
        response = self.post(data='{qqqq')
        self.assertEqual(response.status_code, 400)

    def test_invalid_data_should_give_400(self):
        response = self.post(data={})
        self.assertEqual(response.status_code, 400)

    def test_bad_credentials_should_give_401(self):
        response = self.post(auth_token='bogus')
        self.assertEqual(response.status_code, 401)

    def test_unauthenticated_should_give_401(self):
        response = self.get(use_authentication=False)
        self.assertEqual(response.status_code, 401)

    def test_public_unauthenticated_should_give_200(self):
        response = self.get(
            use_authentication=False,
            view=UnauthenticatedSampleApiView.as_view())
        self.assertEqual(response.status_code, 200)

    def test_unallowed_method_should_give_405(self):
        response = self.put()
        self.assertEqual(response.status_code, 405)
