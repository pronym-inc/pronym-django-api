from json import loads
from copy import deepcopy

from django import forms

from pronym_api.views.model_view import ModelApiView
from pronym_api.views.validator import ModelFormValidator
from pronym_api.test_utils.api_testcase import PronymApiTestCase

from tests.factories import UserAccountFactory
from tests.models import (
    Category, Organization, UserAccount, UserLogEntry, UserProfile)


class CustomCategoryValidator(ModelFormValidator):
    class Meta:
        model = Category
        exclude = ()

    def clean_name(self):
        name = self.cleaned_data['name']
        if name.startswith('q'):
            raise forms.ValidationError("All of our q names are taken, sorry.")
        return name


class CustomUserLogEntryValidator(ModelFormValidator):
    class Meta:
        model = UserLogEntry
        exclude = ()

    def clean_name(self):
        name = self.cleaned_data['name']
        if len(name) == 3:
            raise forms.ValidationError("No 3 letter names.  Sorry!")
        return name


class CustomOrganizationValidator(ModelFormValidator):
    class Meta:
        model = Organization
        exclude = ()

    def clean_name(self):
        name = self.cleaned_data['name']
        if 'Pronym' in name:
            raise forms.ValidationError("Pronym has been banned.  See ya!")
        return name


class CustomUserProfileValidator(ModelFormValidator):
    class Meta:
        model = UserProfile
        exclude = ()

    def clean_email(self):
        email = self.cleaned_data['email']
        if email.endswith('.edu'):
            raise forms.ValidationError("No students allowed!")
        return email


class CustomizedUserAccountModelApiView(ModelApiView):
    endpoint_name = 'customized-user-profile'
    require_authentication = False
    model = UserAccount

    many_to_many_fields = [
        {
            'name': 'categories',
            'validator': CustomCategoryValidator
        }
    ]
    one_to_many_fields = [
        {
            'name': 'log_entries',
            'validator': CustomUserLogEntryValidator
        }
    ]
    many_to_one_fields = [
        {
            'name': 'organization',
            'validator': CustomOrganizationValidator
        }
    ]
    one_to_one_fields = [
        {
            'name': 'profile',
            'validator': CustomUserProfileValidator
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

    def _get_totally_wrong_data(self):
        # Violate the rules for all of our validators.
        bad_data = deepcopy(self.valid_data)
        bad_data['profile']['email'] = 'test@test.edu'
        bad_data['organization']['name'] = 'Pronym Industries'
        bad_data['categories'][0]['name'] = 'quirky'
        bad_data['log_entries'][1]['name'] = 'LOG'
        return bad_data

    def test_uses_custom_validators_on_create(self):
        bad_data = self._get_totally_wrong_data()

        response = self.post(data=bad_data)

        self.assertEqual(response.status_code, 400)

        errors = loads(response.content)['errors']

        self.assertIn('email', errors['profile'])
        self.assertIn('name', errors['organization'])
        self.assertEqual(errors['categories'][0]['index'], 0)
        self.assertIn('name', errors['categories'][0]['errors'])
        self.assertEqual(errors['log_entries'][0]['index'], 1)
        self.assertIn('name', errors['log_entries'][0]['errors'])

    def test_uses_custom_validators_on_modify(self):
        bad_data = self._get_totally_wrong_data()

        account = UserAccountFactory()

        response = self.patch(
            data=bad_data,
            view_kwargs={'id': account.id}
        )

        self.assertEqual(response.status_code, 400)

        errors = loads(response.content)['errors']

        self.assertIn('email', errors['profile'])
        self.assertIn('name', errors['organization'])
        self.assertEqual(errors['categories'][0]['index'], 0)
        self.assertIn('name', errors['categories'][0]['errors'])
        self.assertEqual(errors['log_entries'][0]['index'], 1)
        self.assertIn('name', errors['log_entries'][0]['errors'])

    def test_uses_custom_validators_on_replace(self):
        bad_data = self._get_totally_wrong_data()

        account = UserAccountFactory()

        response = self.put(
            data=bad_data,
            view_kwargs={'id': account.id}
        )

        self.assertEqual(response.status_code, 400)

        errors = loads(response.content)['errors']

        self.assertIn('email', errors['profile'])
        self.assertIn('name', errors['organization'])
        self.assertEqual(errors['categories'][0]['index'], 0)
        self.assertIn('name', errors['categories'][0]['errors'])
        self.assertEqual(errors['log_entries'][0]['index'], 1)
        self.assertIn('name', errors['log_entries'][0]['errors'])
