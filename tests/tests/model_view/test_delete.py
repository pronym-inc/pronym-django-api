from pronym_api.test_utils.api_testcase import PronymApiTestCase

from tests.factories import OrganizationFactory
from tests.models import Organization
from tests.test_views.model_view_sample import OrganizationModelApiView


class ModelViewDeleteTestCase(PronymApiTestCase):
    view_class = OrganizationModelApiView

    def setUp(self):
        PronymApiTestCase.setUp(self)
        self.organization = OrganizationFactory()

    def get_view_kwargs(self):
        return {
            'id': self.organization.id
        }

    def test(self):
        response = self.delete()

        self.assertEqual(response.status_code, 200, response.content)

        try:
            Organization.objects.get(pk=self.organization.id)
        except Organization.DoesNotExist:
            pass
        else:
            self.fail('organization should have been deleted, but was not.')

    def test_non_existent(self):
        response = self.delete(view_kwargs={'id': self.organization.id + 1})

        self.assertEqual(response.status_code, 404)
