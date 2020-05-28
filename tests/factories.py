import factory

from tests.models import (
    Category, Organization, UserAccount, UserProfile, AccountUpdate)


class UserProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserProfile

    email = factory.Sequence(lambda n: "test{0}@test.com".format(n))


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: "Org {0}".format(n))


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: "Category {0}".format(n))


class UserAccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserAccount

    name = factory.Sequence(lambda n: "User {0}".format(n))
    profile = factory.SubFactory(UserProfileFactory)
    organization = factory.SubFactory(OrganizationFactory)


class AccountUpdateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AccountUpdate
