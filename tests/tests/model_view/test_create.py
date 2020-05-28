from json import loads

from pronym_api.test_utils.api_testcase import PronymApiTestCase

from tests.factories import OrganizationFactory
from tests.models import Organization
from tests.test_views.model_view_sample import OrganizationCollectionApiView


class ModelViewCreateTestCase(PronymApiTestCase):
    view_class = OrganizationCollectionApiView

    valid_data = {'name': 'Pronym Inc'}

    def test(self):
        response = self.post()

        self.assertEqual(response.status_code, 200, response.content)

        data = loads(response.content)

        record = Organization.objects.get(pk=data['id'])

        self.assertEqual(record.name, 'Pronym Inc')

    def test_invalid(self):
        # Name has a unique constraint, so we'll violate that.
        OrganizationFactory(name='Pronym Inc')

        response = self.post()

        self.assertEqual(response.status_code, 400, response.content)
