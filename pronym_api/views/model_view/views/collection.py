"""A view governing the collection-level for a database model."""
from abc import ABC
from typing import TypeVar, Generic, Optional, Dict

from django.db.models import Model, QuerySet

from pronym_api.models.owned_model import OwnedModel
from pronym_api.views.actions import ResourceAction
from pronym_api.views.api_view import HttpMethod
from pronym_api.views.model_view.actions.create import CreateModelResourceAction, CreateOwnedModelResourceAction
from pronym_api.views.model_view.actions.search import SearchModelResourceAction
from pronym_api.views.model_view.views.base import BaseModelApiView

ModelT = TypeVar("ModelT", bound=Model)
OwnedModelT = TypeVar("OwnedModelT", bound=OwnedModel)


class ModelCollectionApiView(Generic[ModelT], BaseModelApiView[ModelT, 'QuerySet[ModelT]'], ABC):
    """An API View governing requests at the collection level.. e.g. /api/my_resource/
    as opposed to ModelDetailApiView which would handle requests at the detail level, e.g. /api/my_resource/35/"""
    def _get_action_configuration(self) -> Dict[HttpMethod, ResourceAction]:
        return {
            HttpMethod.GET: SearchModelResourceAction(),
            HttpMethod.POST: CreateModelResourceAction(self._get_model()),
        }

    def _get_endpoint_name(self) -> str:
        return f"{self._get_model().__name__.lower()}-collection"

    def _get_resource(self) -> Optional[QuerySet]:
        return self._get_queryset()


class OwnedModelCollectionApiView(Generic[OwnedModelT], ModelCollectionApiView[OwnedModelT], ABC):
    """An API collection view for owned models that will by default return a queryset filtered
    to the appropriate account."""

    def _get_action_configuration(self) -> Dict[HttpMethod, ResourceAction]:
        config = super()._get_action_configuration()
        config[HttpMethod.POST] = CreateOwnedModelResourceAction(self._get_model())
        return config

    def _get_queryset(self) -> 'QuerySet[OwnedModelT]':
        """Filtered the queryset down to ones owned by the authenticated user."""
        return self._get_model().objects.filter(api_account=self.authenticated_account_member.api_account)
