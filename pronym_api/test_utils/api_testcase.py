from django.test import RequestFactory, TestCase

from .factories import ApiAccountMemberFactory


class PronymApiTestCase(TestCase):
    base_url = '/'
    view_class = None
    valid_data = {}

    def delete(self, **kwargs):
        return self.send_request('delete', **kwargs)

    def get(self, **kwargs):
        return self.send_request('get', **kwargs)

    def get_authentication_headers(self, auth_token=None):
        if auth_token is None:
            auth_token = self.auth_token
        value = "Token {0}".format(auth_token)
        return {'HTTP_AUTHORIZATION': value}

    def get_authenticated_user(self):
        if hasattr(self, 'authenticated_user'):
            return self.authenticated_user

    def get_url(self):
        return self.base_url

    def get_valid_data(self, **data):
        my_data = self.valid_data
        my_data.update(data)
        return my_data

    def post(self, **kwargs):
        return self.send_request('post', **kwargs)

    def put(self, **kwargs):
        return self.send_request('put', **kwargs)

    def setUp(self):
        self.request_factory = RequestFactory()
        if self.should_use_authentication():
            self.account_member = ApiAccountMemberFactory()
            self.whitelist_entry = self.account_member.create_whitelist_entry()
            self.auth_token = self.whitelist_entry.encode()

    def send_request(
            self, method, data=None, url=None, use_authentication=None,
            auth_token=None, view=None, user=None, **data_kwargs):
        if use_authentication is None:
            use_authentication = self.should_use_authentication()
        if data is None:
            data = self.get_valid_data(**data_kwargs)
        request_url = url or self.get_url()
        allowed_methods = ('get', 'patch', 'post', 'put', 'delete')
        if method not in allowed_methods:
            raise Exception('Invalid method: {0}'.format(method))
        kwargs = {'data': data}
        if method in ('patch', 'post', 'put'):
            kwargs['content_type'] = 'application/json'
        if use_authentication:
            kwargs.update(self.get_authentication_headers(auth_token))
        handler = getattr(self.request_factory, method)
        request = handler(request_url, **kwargs)
        if view is None:
            view = self.view_class.as_view()
        if user is None:
            user = self.get_authenticated_user()
        if user is not None:
            request.user = user
        return view(request)

    def should_use_authentication(self):
        return self.view_class.require_authentication
