"""A sample model view setup."""
from typing import Type

from django.db.models import QuerySet

from pronym_api.views.model_view.views import ModelCollectionApiView, ModelDetailApiView

from tests.models import Organization, UserAccount


class OrganizationCollectionApiView(ModelCollectionApiView[Organization]):
    """Fake api view."""
    require_authentication = False

    def _get_model(self) -> Type[Organization]:
        return Organization

    def _get_queryset(self) -> 'QuerySet[Organization]':
        return Organization.objects.all()


class OrganizationDetailApiView(ModelDetailApiView[Organization]):
    """Fake detail view"""
    require_authentication = False

    def _get_model(self) -> Type[Organization]:
        return Organization

    def _get_queryset(self) -> 'QuerySet[Organization]':
        return Organization.objects.all()


class UserAccountCollectionApiView(ModelCollectionApiView[UserAccount]):
    """Faker API view"""
    require_authentication = False

    def _get_model(self) -> Type[UserAccount]:
        return UserAccount

    def _get_queryset(self) -> 'QuerySet[UserAccount]':
        return UserAccount.objects.all()


class UserAccountDetailApiView(ModelDetailApiView[UserAccount]):
    """Faker API view"""
    require_authentication = False

    def _get_model(self) -> Type[UserAccount]:
        return UserAccount

    def _get_queryset(self) -> 'QuerySet[UserAccount]':
        return UserAccount.objects.all()
