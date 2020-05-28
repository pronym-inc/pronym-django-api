"""
Resources are an abstract underlying datatype for an endpoint.  ResourceRouter's manage actions for that endpoint.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, TypeVar, Generic, Union, Any, List, Type, Optional

from django.forms.forms import BaseForm

from pronym_api.models import ApiAccountMember
from pronym_api.views.validation import ApiValidationErrorSummary

ResourceT = TypeVar("ResourceT")
FormT = TypeVar("FormT", bound=BaseForm)


class NullResource:
    """Empty class for requests that don't care about the resource."""


@dataclass
class ApiProcessingFailure:
    """Summary of a failure to process.  `status` should indicate whose fault it is (4xx is them, 5xx is us)"""
    errors: List[str]
    status: int


class BaseAction(Generic[ResourceT], ABC):
    """Base action class."""
    def check_authorization(
            self,
            account_member: ApiAccountMember,
            resource: ResourceT
    ) -> bool:
        """Is the given user allowed to perform this action?  By default, we will allow them in.  There is a check
        at the resource-level, which will usually suffice - but you can override this if you need action-level
        specification of the authorization"""
        return True

    @abstractmethod
    def execute(
            self,
            request: Dict[str, Any],
            account_member: Optional[ApiAccountMember],
            resource: ResourceT
    ) -> Optional[Union[ApiProcessingFailure, Dict[str, Any]]]:
        """Execute this action with these parameters on this resource.  Generally, you will call this after getting
        the request object from the `validate` method."""

    @abstractmethod
    def validate(
            self,
            request_data: Dict[str, Any],
            account_member: Optional[ApiAccountMember],
            resource: ResourceT
    ) -> Union[ApiValidationErrorSummary, Dict[str, Any]]:
        """Validate that the request is valid for this action."""


class ResourceAction(BaseAction[ResourceT], ABC):
    """An action that can be performed on a resource."""
    pass


class NoResourceAction(BaseAction[NullResource], ABC):
    """An action that doesn't involve a resource."""
    @abstractmethod
    def execute(
            self,
            request: Dict[str, Any],
            account_member: Optional[ApiAccountMember],
            resource: NullResource = NullResource()
    ) -> Optional[Union[ApiProcessingFailure, Dict[str, Any]]]:
        """Override with default parameter"""

    @abstractmethod
    def validate(
            self,
            request_data: Dict[str, Any],
            account_member: Optional[ApiAccountMember],
            resource: NullResource = NullResource()
    ) -> Union[ApiValidationErrorSummary, Dict[str, Any]]:
        """Override with default parameter"""


class UnvalidatedResourceAction(Generic[ResourceT], ResourceAction[ResourceT], ABC):
    """A resource action with no validation."""
    def validate(
            self,
            request_data: Dict[str, Any],
            account_member: Optional[ApiAccountMember],
            resource: ResourceT
    ) -> Union[ApiValidationErrorSummary, Dict[str, Any]]:
        """Always return empty dict, never fail to validate."""
        return {}


class FormValidatedResourceAction(Generic[FormT, ResourceT], ResourceAction[ResourceT], ABC):
    """A resource action that uses a form for validation."""
    __form: FormT

    def validate(
            self,
            request_data: Dict[str, Any],
            account_member: Optional[ApiAccountMember],
            resource: ResourceT
    ) -> Union[ApiValidationErrorSummary, Dict[str, Any]]:
        """Use a form to validate the request."""
        form = self._get_form(request_data, account_member, resource)
        if form.is_valid():
            return form.cleaned_data
        else:
            request_errors = [
                error
                for error
                in form.errors.get('__all__', [])
            ]
            field_name: str
            errors: List[str]
            field_errors: Dict[str, Union[Dict[str, Any], List[str]]] = {}
            for field_name, errors in form.errors.items():
                if field_name == '__all__':
                    continue
                if isinstance(errors, dict):
                    field_errors[field_name] = errors
                else:
                    field_errors[field_name] = errors
            return ApiValidationErrorSummary(
                request_errors=request_errors,
                field_errors=field_errors
            )

    def _get_form(
            self,
            request_data: Dict[str, Any],
            account_member: Optional[ApiAccountMember],
            resource: ResourceT
    ) -> FormT:
        """Return the form to use for validation."""
        if not hasattr(self, '__form'):
            form_kwargs = self._get_form_kwargs(request_data, account_member, resource)
            self.__form = self._get_form_class(request_data, account_member, resource)(request_data, **form_kwargs)
        return self.__form

    def _get_form_kwargs(
            self,
            request_data: Dict[str, Any],
            account_member: Optional[ApiAccountMember],
            resource: ResourceT
    ) -> Dict[str, Any]:
        """Get the kwargs to pass to the form."""
        return {}

    @abstractmethod
    def _get_form_class(
            self,
            request_data: Dict[str, Any],
            account_member: Optional[ApiAccountMember],
            resource: ResourceT
    ) -> Type[FormT]:
        """Get the form class to use for validation"""


class NoResourceFormAction(Generic[FormT], FormValidatedResourceAction[FormT, NullResource], ABC):
    """A form action that requires no resource."""
