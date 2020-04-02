from json import loads

from pronym_api.views.api_view import ApiValidationError
from pronym_api.views.processor import Processor

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
        response = self.post(data={})
        self.assertEqual(response.status_code, 400, response.content)

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


class ProcessorValidationErrorProcessor(Processor):
    def process(self):
        raise ApiValidationError({'test': 'test!'})


class ProcessorValidationErrorStatusCodeApiTest(PronymApiTestCase):
    class ProcessorValidationErrorSampleApiView(AuthenticatedSampleApiView):
        methods = {
            'POST': {
                'processor': ProcessorValidationErrorProcessor
            }
        }

    view_class = ProcessorValidationErrorSampleApiView

    def test(self):
        response = self.post()

        self.assertEqual(response.status_code, 400)
        self.assertIn('test', loads(response.content)['errors'])


class UnauthorizedStatusCodeApiTest(PronymApiTestCase):
    class UnauthorizedSampleApiView(AuthenticatedSampleApiView):
        def check_authorization(self):
            return False

    view_class = UnauthorizedSampleApiView

    def test(self):
        response = self.post()

        self.assertEqual(response.status_code, 403)


class BrokenProcessor(Processor):
    def process(self):
        raise Exception


class BrokenStatusCodeApiTest(PronymApiTestCase):

    class BrokenSampleApiView(AuthenticatedSampleApiView):
        methods = {
            'POST': {
                'processor': BrokenProcessor
            }
        }

    view_class = BrokenSampleApiView

    def test_some_internal_exception(self):
        response = self.post()

        self.assertEqual(response.status_code, 500)
