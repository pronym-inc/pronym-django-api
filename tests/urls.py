from django.conf.urls import url

from pronym_api.api.get_token import GetTokenApiView

from tests.test_views.authenticated_sample import (
    AuthenticatedSampleApiView)
from tests.test_views.model_view_sample import OrganizationModelApiView
from tests.test_views.unauthenticated_sample import (
    UnauthenticatedSampleApiView)


urlpatterns = [
    url(r'^get_token/$', GetTokenApiView.as_view(), name='get-token'),
    url(r'^unauth_sample/$',
        UnauthenticatedSampleApiView.as_view(),
        name='unauth-sample'),
    url(r'^sample/$',
        AuthenticatedSampleApiView.as_view(),
        name='sample'),
    url(r'^organization/(?:(?P<id>\d+)/)?',
        OrganizationModelApiView.as_view(),
        name='organization')
]
