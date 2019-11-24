import factory

from pronym_api.models import (
    ApiAccount, ApiAccountMember, LogEntry, TokenWhitelistEntry)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'auth.User'

    username = factory.Sequence(lambda n: "user{0}".format(n))
    first_name = "User"
    last_name = factory.Sequence(lambda n: "{0}".format(n))
    email = factory.Sequence(lambda n: "test{0}@mail.com".format(n))

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        self.set_password(extracted or 'password123')
        self.save()


class ApiAccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ApiAccount

    name = factory.Sequence(lambda n: "Api Account {0}".format(n))


class ApiAccountMemberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ApiAccountMember

    api_account = factory.SubFactory(ApiAccountFactory)
    user = factory.SubFactory(UserFactory)


class LogEntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LogEntry

    endpoint_name = 'sample-endpoint'
    source_ip = '123.123.123.123'
    path = '/test/'
    host = 'example.com'
    port = 443
    is_authenticated = True
    authenticated_profile = factory.SubFactory(ApiAccountMemberFactory)
    request_method = "POST"
    request_headers = '{"test": 1}'
    request_payload = '{"data": 4}'
    response_payload = '{"response": 5}'
    status_code = 200


class TokenWhitelistEntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TokenWhitelistEntry

    api_account_member = factory.SubFactory(ApiAccountMemberFactory)
