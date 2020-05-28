"""Action for creating a new instance of a model.  Will derive a reasonable model form."""
from abc import ABC
from typing import Generic, TypeVar, Type, Dict, Any, Optional, Union

from django.db.models import Model, QuerySet

from pronym_api.models import ApiAccountMember
from pronym_api.models.owned_model import OwnedModel
from pronym_api.views.actions import FormValidatedResourceAction, ApiProcessingFailure
from pronym_api.views.model_view.model_to_dict import rec_model_to_dict
from pronym_api.views.model_view.modelform import LazyModelForm


ResourceT = TypeVar("ResourceT")
ModelT = TypeVar("ModelT", bound=Model)
OwnedModelT = TypeVar("OwnedModelT", bound=OwnedModel)


class BaseSaveModelFormResourceAction(
    Generic[ResourceT],
    FormValidatedResourceAction[LazyModelForm, ResourceT],
    ABC
):
    """Base action that saves a model form."""
    _model: Type[Model]

    def __init__(self, model: Type[Model]):
        self._model = model

    def execute(
            self,
            request: Dict[str, Any],
            account_member: Optional[ApiAccountMember],
            resource: ResourceT
    ) -> Optional[Union[ApiProcessingFailure, Dict[str, Any]]]:
        """Save the model form and serialize the new object."""
        form = self._get_form(request, account_member, resource)
        obj = self._save_form(form, request, account_member, resource)
        return rec_model_to_dict(obj)

    def _save_form(
        self,
        form: LazyModelForm,
        request: Dict[str, Any],
        account_member: Optional[ApiAccountMember],
        resource: ResourceT
    ) -> ModelT:
        # Validate should have already tested that this works, so we'll just do it and move on.
        form.is_valid()
        obj = form.save()
        return obj

    def _get_form_class(
            self,
            request: Dict[str, Any],
            account_member: Optional[ApiAccountMember],
            resource: ResourceT
    ) -> Type[LazyModelForm]:
        return LazyModelForm.for_model(self._model)


class CreateModelResourceAction(Generic[ModelT], BaseSaveModelFormResourceAction['QuerySet[ModelT]']):
    """Action to create a new resource."""


class CreateOwnedModelResourceAction(Generic[OwnedModelT], CreateModelResourceAction[OwnedModelT]):
    """Action to create a new owned resource - will auto-assign the right account."""
    def _save_form(
            self,
            form: LazyModelForm,
            request: Dict[str, Any],
            account_member: Optional[ApiAccountMember],
            resource: ResourceT
    ) -> OwnedModelT:
        # Update the api account on the instance before we save.
        instance: OwnedModel = form.instance
        instance.api_account = account_member.api_account
        return super()._save_form(form, request, account_member, resource)
