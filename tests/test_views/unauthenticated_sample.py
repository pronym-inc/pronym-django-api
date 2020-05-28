"""View for testing unauthenticated functionality."""
from tests.test_views.authenticated_sample import AuthenticatedSampleApiView


class UnauthenticatedSampleApiView(AuthenticatedSampleApiView):
    """An example of an unauthenticated endpoint"""
    require_authentication = False

    def _get_endpoint_name(self) -> str:
        return "unauthenticated-sample"

