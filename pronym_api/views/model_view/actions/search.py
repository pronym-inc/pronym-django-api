"""Base actions for searching a collection."""
from abc import ABC
from typing import Generic, TypeVar, Dict, Any, Optional, Union

from django.db.models import Model, QuerySet

from pronym_api.models import ApiAccountMember
from pronym_api.views.actions import UnvalidatedResourceAction, ApiProcessingFailure
from pronym_api.views.model_view.model_to_dict import rec_model_to_dict

ModelT = TypeVar("ModelT", bound=Model)


class SearchModelResourceAction(
    Generic[ModelT],
    UnvalidatedResourceAction['QuerySet[ModelT]'],
    ABC
):
    """A resource action for searching a collection."""
    def execute(
            self,
            request: Dict[str, Any],
            account_member: Optional[ApiAccountMember],
            resource: 'QuerySet[ModelT]'
    ) -> Optional[Union[ApiProcessingFailure, Dict[str, Any]]]:
        """Do optional filtering and then return the list."""
        filtered_results = self._filter_results(request, account_member, resource)
        return {
            "results": [
                rec_model_to_dict(model) for model in filtered_results
            ]
        }

    def _filter_results(
            self,
            request: Dict[str, Any],
            account_member: Optional[ApiAccountMember],
            resource: 'QuerySet[ModelT]'
    ) -> 'QuerySet[ModelT]':
        """Do some filtering of the results."""
        return resource
