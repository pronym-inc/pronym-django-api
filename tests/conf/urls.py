from django.conf.urls import url

from tests.test_views import SampleApiView


urlpatterns = [
    url(r'^sample/$',
        SampleApiView.as_view(),
        name='sample'),
]
