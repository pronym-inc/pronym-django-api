from datetime import timedelta
from unittest.mock import patch

from django.conf import settings

import jwt

from pronym_api.test_utils.api_testcase import PronymApiTestCase

from tests.test_views.authenticated_sample import (
    AuthenticatedSampleApiView)


class AuthenticationApiTest(PronymApiTestCase):
    view_class = AuthenticatedSampleApiView

    valid_data = {
        'name': 'Gregg',
        'email': 'gregg@mail.com'
    }

    def make_new_token(self, **kwargs):
        jwt_payload = jwt.decode(
            self.whitelist_entry.encode(),
            settings.API_SECRET,
            algorithms=['HS256'],
            audience=settings.JWT_AUD,
            issuer=settings.JWT_ISS)
        jwt_payload.update(kwargs)
        return jwt.encode(
            jwt_payload,
            settings.API_SECRET,
            algorithm='HS256').decode('ascii')

    @patch('pronym_api.models.token_whitelist_entry.now')
    def test_expired_token_should_400(self, now_):
        now_.return_value = self.whitelist_entry.datetime_added + timedelta(
            minutes=settings.TOKEN_EXPIRATION_MINUTES + 1)

        response = self.post()
        self.assertEqual(response.status_code, 401, response.content)

    def test_jwt_token(self):
        # This gets a little into the weeds, but if we mess with
        # various components of the decoded JWT token it should
        # be invalid.
        different_dt = self.whitelist_entry.datetime_added - timedelta(days=1)
        # Check iat, nbf, and exp
        for field in ('iat', 'nbf', 'exp'):
            new_token = self.make_new_token(
                **{field: different_dt.timestamp()})
            response = self.post(auth_token=new_token)
            self.assertEqual(response.status_code, 401, response.content)

        # Check sub and iss
        for field in ('sub', 'iss', 'jti'):
            new_token = self.make_new_token(**{field: '6'})
            response = self.post(auth_token=new_token)
            self.assertEqual(response.status_code, 401, response.content)
