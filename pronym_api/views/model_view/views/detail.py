"""A detail-level view for database models."""
from abc import ABC
from typing import Optional, Dict, TypeVar, Generic

from django.db.models import Model, QuerySet

from pronym_api.models.owned_model import OwnedModel
from pronym_api.views.actions import ResourceAction
from pronym_api.views.api_view import HttpMethod
from pronym_api.views.model_view.actions.delete import DeleteModelResourceAction
from pronym_api.views.model_view.actions.modify import ModifyModelResourceAction
from pronym_api.views.model_view.actions.replace import ReplaceModelResourceAction
from pronym_api.views.model_view.actions.retrieve import RetrieveModelResourceAction
from pronym_api.views.model_view.views.base import BaseModelApiView


ModelT = TypeVar("ModelT", bound=Model)
OwnedModelT = TypeVar("OwnedModelT", bound=OwnedModel)


class ModelDetailApiView(Generic[ModelT], BaseModelApiView[ModelT, ModelT], ABC):
    """An API endpoint for managing specific rows in a database."""
    def _get_action_configuration(self) -> Dict[HttpMethod, ResourceAction]:
        return {
            HttpMethod.GET: RetrieveModelResourceAction(),
            HttpMethod.DELETE: DeleteModelResourceAction(),
            HttpMethod.PUT: ReplaceModelResourceAction(self._get_model()),
            HttpMethod.PATCH: ModifyModelResourceAction(self._get_model())
        }

    def _get_endpoint_name(self) -> str:
        return f"{self._get_model().__name__.lower()}-detail"

    def _get_resource(self) -> Optional[ModelT]:
        results = self._get_queryset().filter(pk=self.kwargs['id'])
        if len(results) == 0:
            return None
        return results[0]


class OwnedModelDetailApiView(Generic[OwnedModelT], ModelDetailApiView[OwnedModelT], ABC):
    """An endpoint for dealing with owned database objects."""
    def _get_queryset(self) -> 'QuerySet[OwnedModelT]':
        """Filtered the queryset down to ones owned by the authenticated user."""
        return self._get_model().objects.filter(api_account=self.authenticated_account_member.api_account)
