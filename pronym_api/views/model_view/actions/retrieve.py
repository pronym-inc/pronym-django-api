"""Retrieve a specific instance of the model."""
from typing import TypeVar, Generic, Dict, Any, Optional, Union

from django.db.models import Model

from pronym_api.models import ApiAccountMember
from pronym_api.views.actions import UnvalidatedResourceAction, ApiProcessingFailure
from pronym_api.views.model_view.model_to_dict import rec_model_to_dict


ModelT = TypeVar("ModelT", bound=Model)


class RetrieveModelResourceAction(Generic[ModelT], UnvalidatedResourceAction[ModelT]):
    """Action to retrieve a specific record."""
    def execute(
        self,
        request: Dict[str, Any],
        account_member: Optional[ApiAccountMember],
        resource: ModelT
    ) -> Optional[Union[ApiProcessingFailure, Dict[str, Any]]]:
        """Just convert model to dict."""
        return rec_model_to_dict(resource)
