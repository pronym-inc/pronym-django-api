from typing import Type, Optional, Dict, Any, Union

from django import forms

from pronym_api.models import ApiAccountMember
from pronym_api.views.actions import NoResourceFormAction, NullResource, ApiProcessingFailure, BaseAction
from pronym_api.views.api_view import NoResourceApiView, ResourceT, HttpMethod


class ExampleForm(forms.Form):
    """Test form for sample."""
    name = forms.CharField()
    email = forms.CharField()
    color = forms.CharField(required=False)


class ExampleResourceAction(NoResourceFormAction[ExampleForm]):
    """Test resource action."""

    def _get_form_class(
            self,
            request: Dict[str, Any],
            account_member: Optional[ApiAccountMember],
            resource: NullResource
    ) -> Type[ExampleForm]:
        return ExampleForm

    def execute(
            self,
            request: Dict[str, Any],
            account_member: Optional[ApiAccountMember],
            resource: NullResource
    ) -> Union[ApiProcessingFailure, Dict[str, Any]]:
        """Return a response of some kind"""
        if request['name'] == "Funkhouse":
            raise IndexError("Wow!  wasn't expecting that.")
        if request['name'] == "Larry":
            return ApiProcessingFailure(
                errors=["No larries allowed"],
                status=409
            )
        return {
            'my_data': f"{request['name']} {request['email']}",
            'chonus': 5
        }


class AuthenticatedSampleApiView(NoResourceApiView):
    """Fake sample view for testing."""

    def _check_authorization_to_resource(self, requester: ApiAccountMember, resource: ResourceT):
        return requester.user.first_name != "Badman"

    def _get_action_configuration(self) -> Dict[HttpMethod, BaseAction]:
        return {
            HttpMethod.GET: ExampleResourceAction(),
            HttpMethod.POST: ExampleResourceAction()
        }

    def _get_endpoint_name(self) -> str:
        return "sample-api"

    redacted_request_payload_fields = ['color']
    redacted_response_payload_fields = ['chonus']
