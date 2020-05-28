"""Tests to verify status codes return properly in different scenarios."""
from json import dumps

from django.test import override_settings

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
        self.assertEqual(response.status_code, 200, response.content)

    def test_invalid_json_should_give_400(self):
        response = self.post(data='{qqqq')
        self.assertEqual(response.status_code, 400, response.content)

    def test_invalid_data_should_give_400(self):
        response = self.post(data='')
        self.assertEqual(response.status_code, 400, response.content)

    def test_non_object_json_should_give_400(self):
        response = self.post(data='[]')
        self.assertEqual(response.status_code, 400)

    def test_bad_credentials_should_give_401(self):
        response = self.post(auth_token='bogus')
        self.assertEqual(response.status_code, 401, response.content)

    def test_unauthenticated_should_give_401(self):
        response = self.get(use_authentication=False)
        self.assertEqual(response.status_code, 401, response.content)

    def test_public_unauthenticated_should_give_200(self):
        response = self.get(
            use_authentication=False,
            view=UnauthenticatedSampleApiView.as_view())
        self.assertEqual(response.status_code, 200, response.content)

    def test_unallowed_method_should_give_405(self):
        response = self.put()
        self.assertEqual(response.status_code, 405, response.content)

    def test_unauthorized_should_give_403(self):
        # Our endpoint is written to not allow anyone who has first name "Badman" in
        self.account_member.user.first_name = "Badman"
        self.account_member.user.save()

        response = self.post()
        self.assertEqual(response.status_code, 403, response.content)

    def test_processing_error_should_relay_error(self):
        # Our endpoint is written to give a processing error when first name is larry in data.
        data = self.valid_data.copy()
        data['name'] = 'Larry'

        response = self.post(data=dumps(data))

        self.assertEqual(response.status_code, 409, response.content)

    def test_unknown_method_should_give_405(self):
        response = self.send_request('head')

        self.assertEqual(response.status_code, 405)

    @override_settings(RAISE_ON_500=False)
    def test_exception_thrown_should_give_500(self):
        # Our endpoint will freak out if the name is "Funkhouse"
        data = self.valid_data.copy()
        data['name'] = 'Funkhouse'

        response = self.post(data=dumps(data))

        self.assertEqual(response.status_code, 500, response.content)
