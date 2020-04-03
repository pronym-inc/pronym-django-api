from json import loads
from copy import deepcopy

from pronym_api.test_utils.api_testcase import PronymApiTestCase

from tests.factories import (
    CategoryFactory, OrganizationFactory, UserAccountFactory)
from tests.models import UserAccount
from tests.test_views.model_view_sample import UserAccountModelApiView


class ModelViewRelationshipsTestCase(PronymApiTestCase):
    view_class = UserAccountModelApiView

    valid_data = {
        'name': 'Gregg Keezles',
        'profile': {
            'email': 'gregg@test.com'
        },
        'organization': {
            'name': 'Pranym'
        },
        'categories': [
            {'name': 'Fun'},
            {'name': 'News'}
        ],
        'log_entries': [
            {'name': 'Login'},
            {'name': 'Logout'},
            {'name': 'Register'}
        ]
    }

    def test_create(self):
        response = self.post()

        self.assertEqual(response.status_code, 200, response.content)

        data = loads(response.content)

        account = UserAccount.objects.get(pk=data['id'])

        self.assertEqual(account.name, 'Gregg Keezles')

        self.assertEqual(account.profile.email, 'gregg@test.com')
        self.assertEqual(account.profile.id, data['profile']['id'])

        self.assertEqual(account.organization.name, 'Pranym')
        self.assertEqual(account.organization.id, data['organization']['id'])

        self.assertEqual(account.categories.count(), 2)
        self.assertEqual(account.categories.filter(name='Fun').count(), 1)
        self.assertEqual(account.categories.filter(name='News').count(), 1)
        self.assertEqual(len(data['categories']), 2)

        self.assertEqual(account.log_entries.count(), 3)
        self.assertEqual(account.log_entries.filter(name='Login').count(), 1)
        self.assertEqual(account.log_entries.filter(name='Logout').count(), 1)
        self.assertEqual(
            account.log_entries.filter(name='Register').count(), 1)
        self.assertEqual(len(data['log_entries']), 3)

    def test_create_with_using_ids(self):
        organization = OrganizationFactory()
        category1 = CategoryFactory()
        category2 = CategoryFactory()

        alt_data = deepcopy(self.valid_data)

        alt_data['organization'] = organization.id
        alt_data['categories'] += [category1.id, category2.id]

        response = self.post(data=alt_data)

        self.assertEqual(response.status_code, 200)

        data = loads(response.content)

        account = UserAccount.objects.get(pk=data['id'])

        self.assertEqual(account.categories.count(), 4)
        self.assertEqual(account.categories.filter(id=category1.id).count(), 1)
        self.assertEqual(account.categories.filter(id=category2.id).count(), 1)

        self.assertEqual(account.organization.id, organization.id)

    def test_create_with_nonexistent_ids(self):
        alt_data = deepcopy(self.valid_data)

        alt_data['organization'] = 934234234234234

        response = self.post(data=alt_data)

        self.assertEqual(response.status_code, 400)

        response_data = loads(response.content)

        self.assertIn('organization', response_data['errors'])

    def test_create_nested_error(self):
        data = deepcopy(self.valid_data)
        data['profile']['email'] = 'testnotanemail'

        response = self.post(data=data)

        self.assertEqual(response.status_code, 400)

        response_data = loads(response.content)

        self.assertIn('email', response_data['errors']['profile'])


class ModelViewRelationshipsModifyTestCase(PronymApiTestCase):
    view_class = UserAccountModelApiView

    valid_data = {
        'name': 'Gregg Keezles',
        'profile': {
            'email': 'greggy@test.com'
        },
        'log_entries': [
            {'name': 'Login'}
        ]
    }

    def setUp(self):
        PronymApiTestCase.setUp(self)
        self.account = UserAccountFactory()
        self.account.categories.add(CategoryFactory())

    def get_view_kwargs(self):
        return {'id': self.account.id}

    def test(self):
        response = self.patch()

        self.assertEqual(response.status_code, 200, response.content)

        data = loads(response.content)

        account = UserAccount.objects.get(id=data['id'])

        self.assertEqual(account.name, 'Gregg Keezles')
        self.assertEqual(account.profile.email, 'greggy@test.com')
        self.assertEqual(len(account.log_entries.all()), 1)
        self.assertEqual(len(account.categories.all()), 1)

    def test_update_categories(self):
        data = {
            'categories': [
                {'name': 'Chunk'},
                {'name': 'Chank'}
            ]
        }

        response = self.patch(data=data)

        self.assertEqual(response.status_code, 200, response.content)

        account = UserAccount.objects.get(id=self.account.id)

        self.assertEqual(len(account.categories.all()), 2)
