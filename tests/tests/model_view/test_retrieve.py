from json import loads

from pronym_api.test_utils.api_testcase import PronymApiTestCase

from tests.factories import OrganizationFactory
from tests.test_views.model_view_sample import OrganizationModelApiView


class ModelViewRetrieveTestCase(PronymApiTestCase):
    view_class = OrganizationModelApiView

    def setUp(self):
        PronymApiTestCase.setUp(self)
        self.organization = OrganizationFactory()

    def get_view_kwargs(self):
        return {
            'id': self.organization.id
        }

    def test(self):
        response = self.get()

        self.assertEqual(response.status_code, 200, response.content)

        data = loads(response.content)

        self.assertEqual(data['id'], self.organization.id)
        self.assertEqual(data['name'], self.organization.name)
        self.assertEqual(data['is_active'], self.organization.is_active)

    def test_non_existent_record(self):
        response = self.get(view_kwargs={'id': self.organization.id + 1})

        self.assertEqual(response.status_code, 404)
