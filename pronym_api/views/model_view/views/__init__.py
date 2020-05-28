"""Base views to use for model views."""

from pronym_api.views.model_view.views.collection import ModelCollectionApiView
from pronym_api.views.model_view.views.detail import ModelDetailApiView

__all__ = ['ModelCollectionApiView', 'ModelDetailApiView']
