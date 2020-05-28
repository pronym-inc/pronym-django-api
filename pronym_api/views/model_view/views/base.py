from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Type

from django.db.models import Model, QuerySet

from pronym_api.views.api_view import ResourceApiView

ModelT = TypeVar("ModelT", bound=Model)
ResourceT = TypeVar("ResourceT")


class BaseModelApiView(Generic[ModelT, ResourceT], ResourceApiView[ResourceT], ABC):
    """Base class for an API view concerned with a database model."""
    @abstractmethod
    def _get_model(self) -> Type[ModelT]:
        """The model class for this endpoint."""

    @abstractmethod
    def _get_queryset(self) -> 'QuerySet[ModelT]':
        """Get the queryset used to look up the model."""
