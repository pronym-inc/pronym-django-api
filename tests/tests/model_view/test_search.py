from json import loads

from pronym_api.test_utils.api_testcase import PronymApiTestCase

from tests.factories import OrganizationFactory
from tests.models import Organization
from tests.test_views.model_view_sample import OrganizationModelApiView


class ModelViewSearchTestCase(PronymApiTestCase):
    view_class = OrganizationModelApiView

    def setUp(self):
        PronymApiTestCase.setUp(self)
        for i in range(3):
            OrganizationFactory()

    def test(self):
        response = self.get()

        self.assertEqual(response.status_code, 200, response.content)

        data = loads(response.content)
        self.assertEqual(len(data['results']), 3)

        for result in data['results']:
            organization = Organization.objects.get(pk=result['id'])
            self.assertEqual(organization.name, result['name'])
            self.assertEqual(organization.is_active, result['is_active'])
