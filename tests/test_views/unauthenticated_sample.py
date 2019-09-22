from .authenticated_sample import AuthenticatedSampleApiView


class UnauthenticatedSampleApiView(AuthenticatedSampleApiView):
    endpoint_name = 'unauthenticated-sample'
    require_authentication = False
