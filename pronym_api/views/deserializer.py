from abc import ABC, abstractmethod
from dataclasses import dataclass
from json import JSONDecodeError, loads
from typing import Any, Dict

from django.http import HttpRequest


@dataclass
class DeserializationException(Exception):
    """Something went wrong while deserializing the request.  `message` should indicate what."""
    message: str


class Deserializer(ABC):
    """A deserializer is responsible for extracting a dictionary of values from a request, e.g. extracting JSON data."""
    @abstractmethod
    def deserialize(self, http_request: HttpRequest) -> Dict[str, Any]:
        """Convert a request into a dictionary of values."""


class JsonDeserializer(Deserializer):
    """A deserializer that tries to decode a dictionary from request body."""
    def deserialize(self, http_request: HttpRequest) -> Dict[str, Any]:
        """Deserialize the body and make sure it's a dictionary."""
        if len(http_request.body) == 0:
            return {}
        try:
            json_obj = loads(http_request.body)
        except JSONDecodeError:
            raise DeserializationException("Could not deserialize a valid JSON body.")
        else:
            if not isinstance(json_obj, dict) or not all(map(lambda x: isinstance(x, str), json_obj.keys())):
                raise DeserializationException("Could not deserialize a valid JSON body.")
            return json_obj


class QueryStringDeserializer(Deserializer):
    """Pull request data from the query string."""
    def deserialize(self, http_request: HttpRequest) -> Dict[str, Any]:
        """Parse query string."""
        return {
            key: value
            for key, value in http_request.GET.items()
        }
