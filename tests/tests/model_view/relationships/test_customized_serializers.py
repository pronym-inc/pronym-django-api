from copy import deepcopy
from json import loads

from pronym_api.views.model_view import ModelApiView
from pronym_api.views.serializer import ModelSerializer
from pronym_api.test_utils.api_testcase import PronymApiTestCase

from tests.factories import (
    CategoryFactory, UserAccountFactory, UserLogEntryFactory)
from tests.models import (
    Category, Organization, UserAccount, UserLogEntry, UserProfile)


class CustomCategorySerializer(ModelSerializer):
    model = Category

    def serialize(self):
        output = ModelSerializer.serialize(self)
        output['category_name'] = output['name']
        del output['name']
        return output


class CustomOrganizationSerializer(ModelSerializer):
    model = Organization

    def serialize(self):
        output = ModelSerializer.serialize(self)
        output['organization_name'] = output['name']
        del output['name']
        return output


class CustomUserLogEntrySerializer(ModelSerializer):
    model = UserLogEntry

    def serialize(self):
        output = ModelSerializer.serialize(self)
        output['log_name'] = output['name']
        del output['name']
        return output


class CustomUserProfileSerializer(ModelSerializer):
    model = UserProfile

    def serialize(self):
        output = ModelSerializer.serialize(self)
        output['contact_email'] = output['email']
        del output['email']
        return output


class CustomizedUserAccountModelApiView(ModelApiView):
    endpoint_name = 'customized-user-profile'
    require_authentication = False
    model = UserAccount

    many_to_many_fields = [
        {
            'name': 'categories',
            'serializer': CustomCategorySerializer
        }
    ]
    one_to_many_fields = [
        {
            'name': 'log_entries',
            'serializer': CustomUserLogEntrySerializer
        }
    ]
    many_to_one_fields = [
        {
            'name': 'organization',
            'serializer': CustomOrganizationSerializer
        }
    ]
    one_to_one_fields = [
        {
            'name': 'profile',
            'serializer': CustomUserProfileSerializer
        }
    ]


class CustomizedValidatorModelApiViewTestCase(PronymApiTestCase):
    view_class = CustomizedUserAccountModelApiView

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

    def setUp(self):
        PronymApiTestCase.setUp(self)
        self.account = UserAccountFactory()
        self.account.categories.add(CategoryFactory())
        self.account.categories.add(CategoryFactory())

        UserLogEntryFactory(user=self.account)
        UserLogEntryFactory(user=self.account)
        UserLogEntryFactory(user=self.account)

    def _validate_response(self, response):
        data = loads(response.content)

        print(data)

        if 'results' in data:
            data = data['results'][0]

        self.assertIn('contact_email', data['profile'])
        self.assertIn('organization_name', data['organization'])
        self.assertIn('category_name', data['categories'][0])
        self.assertIn('log_name', data['log_entries'][0])

    def test_uses_custom_serializers_on_search(self):
        self._validate_response(self.get(data={}))

    def test_uses_custom_serializers_on_create(self):
        self._validate_response(self.post())

    def test_uses_custom_serializers_on_retrieve(self):
        self._validate_response(
            self.get(
                data={},
                view_kwargs={'id': self.account.id}
            )
        )

    def test_uses_custom_serializers_on_modify(self):
        data = deepcopy(self.valid_data)
        del data['log_entries']

        self._validate_response(
            self.patch(
                data=data,
                view_kwargs={'id': self.account.id}
            )
        )

    def test_uses_custom_serializers_on_replace(self):
        self._validate_response(
            self.put(
                view_kwargs={'id': self.account.id}
            )
        )
