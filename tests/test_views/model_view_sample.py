from pronym_api.views.model_view import ModelApiView

from tests.models import Organization, UserAccount


class OrganizationModelApiView(ModelApiView):
    endpoint_name = 'organization'
    require_authentication = False
    model = Organization


class UserAccountModelApiView(ModelApiView):
    endpoint_name = 'user-profile'
    require_authentication = False
    model = UserAccount

    many_to_many_fields = ['categories']
    one_to_many_fields = [
        {
            'name': 'log_entries',
            'minimum': 1
        }
    ]
    many_to_one_fields = ['organization']
    one_to_one_fields = ['profile']
