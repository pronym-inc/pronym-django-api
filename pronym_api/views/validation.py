from dataclasses import dataclass
from typing import Dict, List, Any, Union


@dataclass(frozen=True)
class ApiValidationErrorSummary:
    """A summary of the errors validating the request"""
    request_errors: List[str]
    field_errors: Dict[str, Union[Dict[str, Any], List[str]]]
