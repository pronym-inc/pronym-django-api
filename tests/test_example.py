from django.test import RequestFactory, TestCase

from .test_views import SampleApiView


class ExampleTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_example(self):
        request_data = {'name': 'Gregg', 'email': 'Keithley'}
        request = self.factory.post('/sample/')
        view = SampleApiView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 405)
