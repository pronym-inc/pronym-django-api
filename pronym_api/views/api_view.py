"""
ApiView inherits from generic Django view and should serve as the base class for all Pronym API development.
An ApiView will send a request to an `ApiRoute`, based on request method, for processing.
"""
from abc import ABC, abstractmethod
from enum import Enum
from json import JSONDecodeError, dumps, loads
from typing import Dict, List, Any, Optional, Generic, TypeVar, ClassVar, Union

from django.conf import settings
from django.http import HttpResponse, JsonResponse, HttpRequest
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View

from pronym_api.models import LogEntry, TokenWhitelistEntry, ApiAccountMember
from pronym_api.views.actions import BaseAction, ApiProcessingFailure, NullResource, ResourceAction
from pronym_api.views.deserializer import Deserializer, DeserializationException, JsonDeserializer, \
    QueryStringDeserializer

from pronym_api.views.validation import ApiValidationErrorSummary


ResourceT = TypeVar("ResourceT")
ActionT = TypeVar("ActionT", bound=BaseAction)


class HttpMethod(Enum):
    """
    A collection of known HTTP methods.  Add obscure ones if you find them!
    """
    GET = 'GET'
    POST = 'POST'
    DELETE = 'DELETE'
    PUT = 'PUT'
    PATCH = 'PATCH'
    UNKNOWN = 'UNKNOWN'


@method_decorator(csrf_exempt, name='dispatch')
class ApiView(Generic[ResourceT, ActionT], View, ABC):
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

    # This string will replace fields marked as redacted in logging.
    REDACTED_STRING: ClassVar[str] = "******"
    # Should this endpoint check authentication?
    require_authentication: ClassVar[bool] = True
    # Which headers should not be logged?  By default, don't log the
    # auth header.
    redacted_headers: ClassVar[List[str]] = ['http_authorization']
    # Which fields should we scrub from the request data for logging?
    redacted_request_payload_fields: ClassVar[List[str]] = []
    # Which fields should we scrub from the response data for logging?
    redacted_response_payload_fields: ClassVar[List[str]] = []
    # The ApiAccountMember associated with this request, if authenticated.
    authenticated_account_member: Optional[ApiAccountMember]

    _action: Optional[ActionT]
    _http_method: HttpMethod
    _resource: ResourceT

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.authenticated_account_member = None
        self._resource = None

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        The dispatch method handles an incoming HTTP request before it has been delegated based on the request method.
        Here, we will do various checks to validate the request and, if those are successful, we will attempt to process
        the request and generate a response.
        :param request: The HttpRequest from the user
        :param args:
        :param kwargs:
        :return: The HttpResponse to send back to the user.
        """
        # If we get an unknown HTTP method, we'll 405 later - set it to unknown for now.
        try:
            self._http_method = HttpMethod(self.request.method)
        except ValueError:
            self._http_method = HttpMethod.UNKNOWN
        # Determine the action, typically from request method.
        self._action = self._get_action()
        # Get the response - if we get any kind of error, wrap it as a 500 error.
        try:
            response = self._get_response()
        except Exception as e:
            if settings.RAISE_ON_500:  # pragma: no cover
                raise e
            content = 'Server Error'
            response = HttpResponse(content, status=500)
        # Whatever happened, log it.
        self._create_log_entry(response)
        return response

    def _check_authorization_to_resource(self, requester: ApiAccountMember, resource: ResourceT) -> bool:
        """Is the requesting user authorized to access this resource?"""
        return True

    def _get_action(self) -> Optional[ActionT]:
        if self._http_method not in self._get_allowed_methods():
            return None
        return self._get_action_configuration().get(self._http_method)

    @abstractmethod
    def _get_action_configuration(self) -> Dict[HttpMethod, ActionT]:
        """Get the mapping of HttpMethods to actions."""

    @abstractmethod
    def _get_endpoint_name(self) -> str:
        """
        This endpoint's name, used for logging purposes.
        :return: The name of the endpoint.
        """

    @abstractmethod
    def _get_resource(self) -> Optional[ResourceT]:
        """The resource in question."""

    def _check_authentication(self) -> bool:
        """Checks JWT authentication of user from authorization header.  Also populates
        self.authenticated_account_member if authentication succeeds."""
        self.authenticated_account_member = None
        if not self._should_check_authentication():
            return True
        auth_header = self.request.META.get('HTTP_AUTHORIZATION')
        if auth_header is None:
            return False
        auth_split = auth_header.split()
        if len(auth_split) != 2 or auth_split[0].lower() != 'token':
            return False  # pragma: no cover
        token = auth_split[1]
        self.authenticated_account_member = TokenWhitelistEntry.objects.get_account_member_for_token(token)
        return self.authenticated_account_member is not None

    def _check_authorization(
            self,
            requester: ApiAccountMember,
            resource: Optional[ResourceT],
            action: ActionT
    ) -> bool:
        """Determine if user is authorized to do this thing."""
        return (
                resource is None or
                (
                    self._check_authorization_to_resource(requester, resource) and
                    action.check_authorization(requester, resource)
                )
        )

    def _create_log_entry(self, response: HttpResponse) -> LogEntry:
        """
        Create a log entry for the given HttpResponse.
        :param response: The HttpResponse that will be sent to the user.
        :return: The created log entry.
        """
        header_string = self._get_redacted_header_str()
        redacted_request_payload_string = self._get_redacted_request_payload_str()
        redacted_response_payload_string = self._get_redacted_response_payload_str(response)

        return LogEntry.objects.create(
            endpoint_name=self._get_endpoint_name(),
            source_ip=self.request.META.get(
                'HTTP_X_FORWARDED_FOR', 'Unknown'),
            path=self.request.path,
            host=self.request.get_host(),
            port=self.request.get_port(),
            is_authenticated=self.authenticated_account_member is not None,
            authenticated_profile=self.authenticated_account_member,
            request_method=self.request.method or 'Unknown',
            request_headers=header_string,
            request_payload=redacted_request_payload_string,
            response_payload=redacted_response_payload_string,
            status_code=response.status_code
        )

    def _create_validation_error_response(
            self,
            request_errors: Optional[List[str]],
            field_errors: Optional[Dict[str, Union[List[str], Dict[str, Any]]]],
            status: int = 400
    ) -> HttpResponse:
        """
        Generate the error response for this endpoint.
        :param request_errors: Errors that apply to the request as a whole (e.g. span multiple fields or bad JSON)
        :param field_errors: Errors specific to individual fields, keyed by field name.
        :param status: The HTTP status code that should be returned in the response
        :return: The generated HttpResponse
        """
        response_data: Dict[str, Any] = {}
        if request_errors is not None:
            response_data['request_errors'] = request_errors
        if field_errors is not None:
            response_data['field_errors'] = field_errors
        return JsonResponse(response_data, status=status)

    @property
    def _deserializer(self) -> Deserializer:
        if self.request.method == 'GET':
            return QueryStringDeserializer()
        else:
            return JsonDeserializer()

    def _deserialize(self) -> Dict[str, Any]:
        return self._deserializer.deserialize(self.request)

    def _get_response(self) -> HttpResponse:
        # Check authentication, if we need to.
        if not self._check_authentication():
            return HttpResponse(status=401)
        # Does the requested resource exist?
        resource = self._get_resource()
        if resource is None:
            return HttpResponse(status=404)
        self._resource = resource
        # Are you performing an action that exists?
        if self._action is None:
            return HttpResponse(status=405)
        # Are you allowed to perform that action?
        if self.authenticated_account_member is not None:
            if not self._check_authorization(self.authenticated_account_member, resource, self._action):
                return HttpResponse(status=403)
        # Is your request valid?  First, we check if we can even parse the response...
        try:
            request_data = self._deserialize()
        except DeserializationException as e:
            return self._create_validation_error_response(
                request_errors=[e.message],
                field_errors=None,
                status=400
            )
        # Then, if we can parse it, is the response a valid one?
        validation_result = self._action.validate(request_data, self.authenticated_account_member, self._resource)
        if isinstance(validation_result, ApiValidationErrorSummary):
            return self._create_validation_error_response(
                request_errors=validation_result.request_errors,
                field_errors=validation_result.field_errors,
                status=400
            )
        # If we're here, the request is valid, so we can try to process it.
        # It's possible something still goes wrong - it could be their fault or our fault (some errors cannot be
        # detected before you try to process the request - like charging a credit card).  When you return your
        # ApiProcessingFailure, you should specify  if it's our fault (500 response) or their fault (400 response).
        result = self._action.execute(request_data, self.authenticated_account_member, self._resource)
        if isinstance(result, ApiProcessingFailure):
            # Our status will determine status code, indicating whether its our fault or their fault.
            return self._create_validation_error_response(
                request_errors=result.errors,
                field_errors=None,
                status=result.status
            )
        # We made it!  Our request processed successfully.  Send back a 200.
        return self._generate_response(result, 200)

    def _generate_response(self, response_data: Optional[Dict[str, Any]], status_code: int) -> HttpResponse:
        """
        Generate a response back to the user
        :param response_data: The payload to be sent as JSON
        :param status_code: The status code to send to the user
        :return: The generated HttpResponse
        """
        if response_data is None:
            return HttpResponse(status=status_code)
        else:
            return JsonResponse(response_data, status=status_code)

    def _get_allowed_methods(self) -> List[HttpMethod]:
        """Return the list of allowed http methods."""
        return [
            HttpMethod.GET,
            HttpMethod.POST,
            HttpMethod.DELETE,
            HttpMethod.POST,
            HttpMethod.PUT,
            HttpMethod.PATCH
        ]

    def _get_redacted_request_payload_fields(self) -> List[str]:
        """
        A list of request fields to redact in the logs - make use of this to hide passwords or other secrets from the
        log.
        :return: A list of field names to redact.
        """
        return self.redacted_request_payload_fields

    def _get_redacted_response_payload_fields(self) -> List[str]:
        """
        A list of fields in the response to redact.  Good way to hide API tokens and such.
        :return: A list of field names to redact.
        """
        return self.redacted_response_payload_fields

    def _should_check_authentication(self) -> bool:
        """
        :return: Whether or not this endpoint should require authentication and 401 if the user is unauthenticated.
        """
        return self.require_authentication

    def _get_redacted_header_str(self) -> str:
        header_components = []
        for name, value in self.request.META.items():
            if name.lower() in self.redacted_headers:
                cleaned_value = self.REDACTED_STRING
            else:
                cleaned_value = value
            header_components.append(
                "{0}={1}".format(name, cleaned_value))
        return "\n".join(header_components)

    def _get_redacted_response_payload_str(self, response: HttpResponse) -> str:
        if len(response.content) == 0:
            return ''
        try:
            payload_copy = loads(response.content)
        except JSONDecodeError:  # pragma: no cover
            return "Could not deserialize body."
        for redacted_key in self._get_redacted_response_payload_fields():
            if redacted_key in payload_copy:
                payload_copy[redacted_key] = self.REDACTED_STRING
        return dumps(payload_copy)

    def _get_redacted_request_payload_str(self) -> str:
        if self.request.method == 'GET':
            return ""
        try:
            payload_copy = loads(self.request.body)
        except JSONDecodeError:
            return ""
        for redacted_key in self._get_redacted_request_payload_fields():
            if redacted_key in payload_copy:
                payload_copy[redacted_key] = self.REDACTED_STRING
        return dumps(payload_copy)


class NoResourceApiView(ApiView[NullResource, BaseAction], ABC):
    """An API view that doesn't care about resources."""
    def _get_resource(self) -> Optional[NullResource]:
        return NullResource()


class ResourceApiView(Generic[ResourceT], ApiView[ResourceT, ResourceAction], ABC):
    """An API view that cares about a resource."""
