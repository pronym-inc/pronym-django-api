from json import JSONDecodeError, dumps, loads

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View

from pronym_api.models import LogEntry, TokenWhitelistEntry

from .exceptions import ApiValidationError
from .processor import NullProcessor
from .serializer import NullSerializer
from .validator import NullValidator


@method_decorator(csrf_exempt, name='dispatch')
class ApiView(View):
    """A basic view for supply an JSON-based API.  The three primary concepts for
    the ApiView are validators, processors, and serializers.

    The flow of a request into an API View is as follows:

    1) Check to see if request method is allowed.  If not, send 405.
    2) Check to see if user is authorized.  If not, send 401.
    3) Extra raw request data:
    For requests with a body (e.g. POST, PUT, PATCH, etc. requests), the body
    is deserialized as JSON.  For GET requests, the query string will be
    converted into a dictionary and fed into the validator.

    4) Raw request data is fed into the VALIDATOR, which will either trigger
    validation errors and send a 400 response.  If validation is successful,
    we now have the cleaned data.
    5) The validated validator is then passed to the PROCESSOR, which will do
    something (or not) with the data and generate a PROCESSING ARTIFACT.
    Things that might be done by the processor:

    - In the case of a GET query, return (as the processing artifact) a set of
    objects based on the data passed in the querystring.
    - In the case of a POST query, use the validated data to create a new
    record in the database and return the new object as the processing artifact

    6) The validator and processing artifact are then passed to the SERIALIZER,
    which will determine the final response sent in the request.
    7) The serialized data is then encoded to JSON and sent back in the
    successful response."""

    # This is a dictionary mapping request methods (all caps) with
    # the validators, processors, and serializers associated with them.
    # The contents of this dictionary will both determine which methods
    # are allowed on the object (absent methods will be prohibited)
    # and how those requests will be processed.
    # For example, to enable an endpoint that allows GET, POST requests
    # you might specify it like:
    #
    # methods = {
    #     'GET': {
    #         'validator': MyGetValidator,
    #         'processor': MyGetProcessor,
    #         'serializer': MyObjectSerializer
    #     },
    #     'POST': {
    #         'validator': MyPostValidator,
    #         'processor': MyPostProcessor,
    #         'serializer': MyObjectSerializer
    #     }
    # }
    #
    # PUT or DELETE requests to this endpoint will receive a 405 error.
    methods = {}
    # This string will replace fields marked as redacted in logging.
    REDACTED_STRING = "******"
    # Should this endpoint check authentication?
    require_authentication = True
    # Which headers should not be logged?  By default, don't log the
    # auth header.
    redacted_headers = ['http_authorization']
    # Which fields should we scrub from the request data for logging?
    redacted_request_payload_fields = []
    # Which fields should we scrub from the response data for logging?
    redacted_response_payload_fields = []

    def __init__(self, *args, **kwargs):
        View.__init__(self, *args, **kwargs)
        self.authenticated_account_member = None

    def check_authentication(self):
        """Checks JWT authentication of user from authorization
        header.  Also populates self.authenticated_account_member
        if authentication succeeds."""
        self.authenticated_account_member = None
        if not self.should_check_authentication():
            return True
        auth_header = self.request.META.get('HTTP_AUTHORIZATION')
        if auth_header is None:
            return False
        auth_split = auth_header.split()
        if len(auth_split) != 2 or auth_split[0].lower() != 'token':
            return False  # pragma: no cover
        token = auth_split[1]
        self.authenticated_account_member = TokenWhitelistEntry\
            .objects.get_account_member_for_token(token)
        return self.authenticated_account_member is not None

    def check_authorization(self):
        return True

    def check_method_allowed(self):
        return bool(self.get_method_config())

    def check_resource_exists(self):
        return True

    def create_log_entry(self, response):
        header_string = self.get_redacted_header_str()
        redacted_request_payload_string = \
            self.get_redacted_request_payload_str()
        redacted_response_payload_string = \
            self.get_redacted_response_payload_str(response)

        return LogEntry.objects.create(
            endpoint_name=self.get_endpoint_name(),
            source_ip=self.request.META.get(
                'HTTP_X_FORWARDED_FOR', 'Unknown'),
            path=self.request.path,
            host=self.request.get_host(),
            port=self.request.get_port(),
            is_authenticated=self.authenticated_account_member is not None,
            authenticated_profile=self.authenticated_account_member,
            request_method=self.request.method,
            request_headers=header_string,
            request_payload=redacted_request_payload_string,
            response_payload=redacted_response_payload_string,
            status_code=response.status_code
        )

    def create_validation_error_response(
            self, validation_exception, status=400):
        response_data = {
            'errors': validation_exception.errors
        }
        return JsonResponse(response_data, status=status)

    def dispatch(self, request, *args, **kwargs):
        try:
            # Check if this method is allowed on this endpoint.
            if not self.check_method_allowed():
                response = HttpResponse(status=405)
            # Check if the user is allowed to be here.
            elif not self.check_authentication():
                response = HttpResponse(status=401)
            elif not self.check_authorization():
                response = HttpResponse(status=403)
            elif not self.check_resource_exists():
                response = HttpResponse(status=404)
            else:
                # Validate the request data
                try:
                    validator = self.validate_request()
                except ApiValidationError as e:
                    response = self.create_validation_error_response(e)
                else:
                    # This is the happy path - we've made it through
                    # authorization and validation, now generate the success
                    # response.
                    # Process the data
                    # We can also throw an error here.
                    try:
                        self.processing_artifact = self.process(validator)
                    except ApiValidationError as e:
                        response = self.create_validation_error_response(e)
                    else:
                        # Serialize the data
                        response_data = self.serialize(
                            validator, self.processing_artifact)
                        response = self.generate_response(response_data)
        except Exception as e:
            if settings.RAISE_ON_500:  # pragma: no cover
                raise e
            else:
                content = 'Server Error'
            response = HttpResponse(content, status=500)
        self.create_log_entry(response)
        return response

    def generate_response(self, response_data, status_code=None):
        if status_code is None:
            status_code = self.get_status_code()
        return JsonResponse(response_data, status=status_code)

    def get_endpoint_name(self):
        return self.endpoint_name

    def get_methods(self):
        return self.methods

    def get_method_config(self):
        return self.get_methods().get(self.request.method, {})

    def get_processor(self, validator, authenticated_account_member):
        process_cls = self.get_processor_class()
        return process_cls(self, validator)

    def get_processor_class(self):
        return self.get_method_config().get('processor', NullProcessor)

    def get_raw_request_data(self):
        if not hasattr(self, '_raw_request_data'):
            if self.request.method == 'GET':
                # We use the GET data, but by default we'll get back entries
                # as lists, which can be problematic.  So we have to do some
                # conversion.  We will assume we're always just getting 1 value
                # per parameter.
                self._raw_request_data = {
                    key: (
                        value_list[0]
                        if isinstance(value_list, list)
                        else value_list)
                    for key, value_list in self.request.GET.items()
                }
            elif self.request.method == 'DELETE':
                self._raw_request_data = {}
            else:
                if len(self.request.body) == 0:  # pragma: no cover
                    self._raw_request_data = {}
                else:
                    self._raw_request_data = loads(self.request.body)
        return self._raw_request_data

    def get_redacted_header_str(self):
        header_components = []
        for name, value in self.request.META.items():
            if name.lower() in self.redacted_headers:
                cleaned_value = self.REDACTED_STRING
            else:
                cleaned_value = value
            header_components.append(
                "{0}={1}".format(name, cleaned_value))
        return "\n".join(header_components)

    def get_redacted_request_payload_fields(self):
        return self.redacted_request_payload_fields

    def get_redacted_request_payload_str(self):
        if self.request.method == 'GET':
            return ''
        try:
            payload_copy = self.get_raw_request_data().copy()
        except JSONDecodeError:
            return ""
        for redacted_key in self.get_redacted_request_payload_fields():
            if redacted_key in payload_copy:
                payload_copy[redacted_key] = self.REDACTED_STRING
        return dumps(payload_copy)

    def get_redacted_response_payload_fields(self):
        return self.redacted_response_payload_fields

    def get_redacted_response_payload_str(self, response):
        if len(response.content) == 0:
            return ''
        try:
            payload_copy = loads(response.content)
        except JSONDecodeError:  # pragma: no cover
            return response.content
        for redacted_key in self.get_redacted_response_payload_fields():
            if redacted_key in payload_copy:
                payload_copy[redacted_key] = self.REDACTED_STRING
        return dumps(payload_copy)

    def get_serializer(self, validator, processing_artifact):
        serializer_cls = self.get_serializer_class()
        return serializer_cls(self, validator, processing_artifact)

    def get_serializer_class(self):
        return self.get_method_config().get('serializer', NullSerializer)

    def get_status_code(self):
        return 200

    def get_validator(self, data, **validator_kwargs):
        validator_cls = self.get_validator_class()
        return validator_cls(self, data, **validator_kwargs)

    def get_validator_class(self):
        return self.get_method_config().get('validator', NullValidator)

    def get_validator_kwargs(self):
        return {}

    def process(self, validator):
        processor = self.get_processor(
            validator, self.authenticated_account_member)
        artifact = processor.process()
        return artifact

    def serialize(self, validator, processing_artifact):
        serializer = self.get_serializer(validator, processing_artifact)
        return serializer.serialize()

    def should_check_authentication(self):
        return self.require_authentication

    def validate_request(self):
        try:
            request_data = self.get_raw_request_data()
        except JSONDecodeError as e:
            raise ApiValidationError(
                {
                    'json': [
                        'Could not decode a valid JSON request: {0}'.format(e)
                    ]
                }
            )
        validator_kwargs = self.get_validator_kwargs()
        validator = self.get_validator(request_data, **validator_kwargs)
        if not validator.validate():
            raise ApiValidationError(validator.errors)
        return validator
