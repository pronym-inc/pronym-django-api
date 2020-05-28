from json import loads

from pronym_api.test_utils.api_testcase import PronymApiTestCase

from tests.test_views.authenticated_sample import (
    AuthenticatedSampleApiView)


class LoggingApiTest(PronymApiTestCase):
    view_class = AuthenticatedSampleApiView

    valid_data = {
        'name': 'Gregg',
        'email': 'gregg@mail.com'
    }

    def test_should_create_a_log_entry_for_authenticated_request(self):
        self.post(color='red')
        entry = self.account_member.log_entries.all()[0]

        self.assertEqual(entry.status_code, 200)
        self.assertEqual(entry.endpoint_name, "sample-api")
        self.assertEqual(entry.source_ip, 'Unknown')
        self.assertEqual(entry.path, '/')
        self.assertEqual(entry.host, 'testserver')
        self.assertEqual(entry.port, 80)
        self.assertTrue(entry.is_authenticated)
        self.assertEqual(entry.request_method, 'POST')
        self.assertIn(
            'HTTP_AUTHORIZATION=******',
            entry.request_headers)
        self.assertEqual(
            loads(entry.request_payload),
            {'name': 'Gregg', 'email': 'gregg@mail.com', 'color': '******'}
        )
        self.assertEqual(
            loads(entry.response_payload),
            {'my_data': 'Gregg gregg@mail.com', 'chonus': '******'}
        )
