from django import forms

from pronym_api.views import ApiView
from pronym_api.views.processor import Processor
from pronym_api.views.serializer import Serializer
from pronym_api.views.validator import FormValidator


class TestValidator(FormValidator):
    name = forms.CharField()
    color = forms.CharField(required=False)
    email = forms.CharField(required=False)


class TestProcessor(Processor):
    def process(self):
        data = self.validator.cleaned_data
        return "{0} {1}".format(data['name'], data['email'])


class TestSerializer(Serializer):
    def serialize(self):
        return {
            'my_data': self.processing_artifact,
            'chonus': 5
        }


class AuthenticatedSampleApiView(ApiView):
    endpoint_name = 'sample-api'

    methods = {
        'GET': {
            'validator': TestValidator,
            'processor': TestProcessor,
            'serializer': TestSerializer
        },
        'POST': {
            'validator': TestValidator,
            'processor': TestProcessor,
            'serializer': TestSerializer
        }
    }

    redacted_request_payload_fields = ['color']
    redacted_response_payload_fields = ['chonus']
