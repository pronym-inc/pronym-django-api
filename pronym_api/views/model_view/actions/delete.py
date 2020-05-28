"""Action for deleting an object."""
from typing import Generic, TypeVar, Dict, Any, Optional, Union

from django.db.models import Model

from pronym_api.models import ApiAccountMember
from pronym_api.views.actions import UnvalidatedResourceAction, ApiProcessingFailure

ModelT = TypeVar("ModelT", bound=Model)


class DeleteModelResourceAction(Generic[ModelT], UnvalidatedResourceAction[ModelT]):
    """An action for deleting a resource."""
    def execute(
            self,
            request: Dict[str, Any],
            account_member: Optional[ApiAccountMember],
            resource: ModelT
    ) -> Optional[Union[ApiProcessingFailure, Dict[str, Any]]]:
        """Delete the record."""
        resource.delete()
        return None
