from json import loads

from pronym_api.test_utils.api_testcase import PronymApiTestCase

from tests.factories import OrganizationFactory
from tests.models import Organization
from tests.test_views.model_view_sample import OrganizationDetailApiView


class ModelViewReplaceTestCase(PronymApiTestCase):
    view_class = OrganizationDetailApiView

    valid_data = {
        'name': 'Pronym Corp',
        'is_active': False
    }

    def setUp(self):
        PronymApiTestCase.setUp(self)
        self.organization = OrganizationFactory(name='Pronym CCP')

    def get_view_kwargs(self):
        return {
            'id': self.organization.id
        }

    def test(self):
        response = self.put()

        self.assertEqual(response.status_code, 200, response.content)

        data = loads(response.content)

        record = Organization.objects.get(pk=data['id'])

        self.assertEqual(record.id, self.organization.id)
        self.assertEqual(record.name, 'Pronym Corp')
        self.assertFalse(record.is_active)

    def test_invalid(self):
        # Name has a unique constraint, so we'll violate that.
        OrganizationFactory(name='Pronym Inc')

        response = self.put(data={'name': 'Pronym Inc'})

        self.assertEqual(response.status_code, 400, response.content)

    def test_non_existent(self):
        response = self.put(view_kwargs={'id': self.organization.id + 1})

        self.assertEqual(response.status_code, 404)

    def test_require_all_fields(self):
        incomplete_data = self.valid_data.copy()
        del incomplete_data['name']

        response = self.put(data=incomplete_data)

        self.assertEqual(response.status_code, 400, response.content)
