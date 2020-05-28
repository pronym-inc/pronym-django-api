"""Action for modifying/patching a model resource."""
from typing import Generic, TypeVar, Type, Dict, Any, Optional

from django.db.models import Model

from pronym_api.models import ApiAccountMember
from pronym_api.views.model_view.actions.replace import ReplaceModelResourceAction


ModelT = TypeVar("ModelT", bound=Model)


class ModifyModelResourceAction(Generic[ModelT], ReplaceModelResourceAction[ModelT]):
    """Patch a resource.  Omitted fields are not changed."""
    def _get_form_kwargs(self, request_data: Dict[str, Any], account_member: Optional[ApiAccountMember],
                         resource: ModelT) -> Dict[str, Any]:
        kwargs = super()._get_form_kwargs(request_data, account_member, resource)
        kwargs['patch_mode'] = True
        return kwargs
