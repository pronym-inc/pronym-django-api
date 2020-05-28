"""Action for replacing the contents of an instance."""
from typing import Dict, Any, Optional, TypeVar, Generic

from django.db.models import Model

from pronym_api.models import ApiAccountMember
from pronym_api.views.model_view.actions.create import BaseSaveModelFormResourceAction

ModelT = TypeVar("ModelT", bound=Model)


class ReplaceModelResourceAction(Generic[ModelT], BaseSaveModelFormResourceAction[ModelT]):
    """Fully replace the contents of a model with the request data.  Omitted fields will be blank on the new version."""
    def _get_form_kwargs(
            self,
            request_data: Dict[str, Any],
            account_member: Optional[ApiAccountMember],
            resource: ModelT
    ) -> Dict[str, Any]:
        return {'instance': resource}
