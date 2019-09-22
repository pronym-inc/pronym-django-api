from django import forms

from pronym_api.models import ApiAccountMember
from pronym_api.views.api_view import ApiView
from pronym_api.views.processor import Processor
from pronym_api.views.serializer import Serializer
from pronym_api.views.validator import FormValidator


class GetTokenValidator(FormValidator):
    username = forms.CharField()
    password = forms.CharField()

    def clean(self):
        data = self.cleaned_data
        invalid_error = 'Invalid username/password.'
        if 'username' in data and 'password' in data:
            try:
                account_member = ApiAccountMember.objects.get(
                    user__username=data['username'])
            except ApiAccountMember.DoesNotExist:
                raise forms.ValidationError(invalid_error)
            if not account_member.user.check_password(data['password']):
                raise forms.ValidationError(invalid_error)
            self.found_api_account_member = account_member
        return data


class GetTokenProcessor(Processor):
    def process(self):
        # Generate the token
        member = self.validator.found_api_account_member
        return member.create_whitelist_entry()


class GetTokenSerializer(Serializer):
    def serialize(self):
        whitelist_entry = self.processing_artifact
        return {
            "token": whitelist_entry.encode(),
            "expires": whitelist_entry.get_expiration_date().strftime(
                "%Y-%m-%dT%H:%M:%SZ")
        }


class GetTokenApiView(ApiView):
    endpoint_name = 'get-token'
    methods = {
        'POST': {
            'validator': GetTokenValidator,
            'processor': GetTokenProcessor,
            'serializer': GetTokenSerializer
        }
    }
    require_authentication = False

    redacted_request_payload_fields = ['password']
    redacted_response_payload_fields = ['token']
