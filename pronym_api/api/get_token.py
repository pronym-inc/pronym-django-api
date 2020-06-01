"""
An endpoint for users to receive a token to use for future authentication.
"""
from typing import Optional, Dict, Any, Union, Type, ClassVar

from django import forms

from pronym_api.models import ApiAccountMember
from pronym_api.views.actions import BaseAction, NullResource, ApiProcessingFailure, NoResourceFormAction
from pronym_api.views.api_view import NoResourceApiView, HttpMethod


class CreateTokenForm(forms.Form):
    """Validate a CreateToken request."""
    found_api_account_member: Optional[ApiAccountMember]
    username = forms.CharField()
    password = forms.CharField()

    def clean(self):
        """
        Validate that the provided username and password belong to API Account member.
        """
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
        return data


class CreateTokenResourceAction(NoResourceFormAction[CreateTokenForm]):
    """Action to validate username and password and send back a token."""
    def check_authorization(self, account_member: ApiAccountMember, resource: NullResource) -> bool:
        """This will always be called unauthenticated."""
        return True

    def execute(
            self,
            request: Dict[str, Any],
            account_member: Optional[ApiAccountMember],
            resource: NullResource
    ) -> Union[ApiProcessingFailure, Dict[str, Any]]:
        """Create a token for the user and send them back some info."""
        member: ApiAccountMember = ApiAccountMember.objects.get(user__username=request['username'])
        whitelist_entry = member.create_whitelist_entry()
        return {
            "token": whitelist_entry.encode(),
            "expires": whitelist_entry.get_expiration_date().strftime(
                "%Y-%m-%dT%H:%M:%SZ")
        }

    def _get_form_class(
            self,
            request: Dict[str, Any],
            account_member: Optional[ApiAccountMember],
            resource: NullResource
    ) -> Type[CreateTokenForm]:
        return CreateTokenForm


class GetTokenApiView(NoResourceApiView):
    """An endpoint to retrieve a token."""
    require_authentication: ClassVar[bool] = True

    def _get_action_configuration(self) -> Dict[HttpMethod, BaseAction]:
        return {
            HttpMethod.POST: CreateTokenResourceAction()
        }

    def _get_endpoint_name(self) -> str:
        return 'get-token'
