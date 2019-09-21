from django.conf.urls import url

from tests.test_views.sample import SampleApiView


urlpatterns = [
    url(r'^sample/$',
        SampleApiView.as_view(),
        name='sample'),
]
