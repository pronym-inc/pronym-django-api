from pronym_api.views.model_view import ModelApiView

from tests.models import Organization


class OrganizationModelApiView(ModelApiView):
    endpoint_name = 'organization'
    require_authentication = False
    model = Organization
