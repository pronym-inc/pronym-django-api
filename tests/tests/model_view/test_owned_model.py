from json import loads
from typing import Type

from django.test import TestCase

from pronym_api.test_utils.api_testcase import PronymApiTestCase
from pronym_api.views.model_view.views.collection import OwnedModelCollectionApiView
from pronym_api.views.model_view.views.detail import OwnedModelDetailApiView

from tests.factories import AccountUpdateFactory
from tests.models import AccountUpdate


class AccountUpdateApiCollectionView(OwnedModelCollectionApiView[AccountUpdate]):
    """Collection view to demonstrate owned model."""
    def _get_model(self) -> Type[AccountUpdate]:
        return AccountUpdate


class AccountUpdateApiDetailView(OwnedModelDetailApiView[AccountUpdate]):
    """Collection view to demonstrate owned model."""
    def _get_model(self) -> Type[AccountUpdate]:
        return AccountUpdate


class OwnedModelCollectionApiViewTestCase(PronymApiTestCase):
    view_class = AccountUpdateApiCollectionView

    valid_data = {}

    def setUp(self):
        PronymApiTestCase.setUp(self)
        self.account_update = AccountUpdateFactory(api_account=self.account_member.api_account)
        self.foreign_account_update = AccountUpdateFactory()

    def test_search(self):
        response = self.get()

        self.assertEqual(response.status_code, 200, response.content)

        data = loads(response.content)
        ids = list(map(
            lambda update: update['id'],
            data['results']
        ))
        self.assertIn(self.account_update.id, ids)
        self.assertNotIn(self.foreign_account_update.id, ids)

    def test_create(self):
        response = self.post(data={"name": "Greggius"})

        self.assertEqual(response.status_code, 200, response.content)

        db_id = loads(response.content)['id']

        db_instance = AccountUpdate.objects.get(pk=db_id)

        self.assertEqual(db_instance.api_account, self.account_member.api_account)


class OwnedModelDetailApiViewTestCase(PronymApiTestCase):
    view_class = AccountUpdateApiDetailView

    valid_data = {}

    def setUp(self):
        PronymApiTestCase.setUp(self)
        self.account_update = AccountUpdateFactory(api_account=self.account_member.api_account)
        self.foreign_account_update = AccountUpdateFactory()

    def get_view_kwargs(self):
        return {'id': self.account_update.id}

    def test_retrieve_mine(self):
        response = self.get()

        self.assertEqual(response.status_code, 200, response.content)

        data = loads(response.content)
        self.assertEqual(data['id'], self.account_update.id)

    def test_retrieve_other(self):
        response = self.get(view_kwargs={'id': self.foreign_account_update.id})

        self.assertEqual(response.status_code, 404)

    def test_delete_mine(self):
        response = self.delete()

        self.assertEqual(response.status_code, 200, response.content)

        # Should not be able to get the model from the database, because it's been deleted.
        try:
            AccountUpdate.objects.get(pk=self.account_update.id)
        except AccountUpdate.DoesNotExist:
            pass
        else:
            self.fail("Model wasn't deleted, but it should have been.")

    def test_delete_other(self):
        response = self.delete(view_kwargs={'id': self.foreign_account_update.id})

        self.assertEqual(response.status_code, 404)

    def test_modify_mine(self):
        response = self.patch(data={'name': 'Modified'})

        self.assertEqual(response.status_code, 200, response.content)

        obj = AccountUpdate.objects.get(pk=self.account_update.id)
        self.assertEqual(obj.name, 'Modified')

    def test_modify_other(self):
        response = self.patch(data={'name': 'Nanana'}, view_kwargs={'id': self.foreign_account_update.id})

        self.assertEqual(response.status_code, 404)

    def test_replace_mine(self):
        response = self.put(data={'name': 'Modified'})

        self.assertEqual(response.status_code, 200, response.content)

        obj = AccountUpdate.objects.get(pk=self.account_update.id)
        self.assertEqual(obj.name, 'Modified')

    def test_replace_other(self):
        response = self.put(data={'name': 'Nanana'}, view_kwargs={'id': self.foreign_account_update.id})

        self.assertEqual(response.status_code, 404)


class OwnedModelManagerTestCase(PronymApiTestCase):
    view_class = AccountUpdateApiDetailView

    def setUp(self):
        PronymApiTestCase.setUp(self)
        self.account_update = AccountUpdateFactory(api_account=self.account_member.api_account)
        self.foreign_account_update = AccountUpdateFactory()

    def test_get_records_owned_by_account(self):
        qs = AccountUpdate.objects.get_records_owned_by_account(self.account_member.api_account)
        self.assertIn(self.account_update, qs)
        self.assertNotIn(self.foreign_account_update, qs)
