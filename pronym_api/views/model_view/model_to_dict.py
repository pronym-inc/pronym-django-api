"""A recursive implementation of model_to_dict to serialize nested related fields."""
from typing import Dict, Any

from django.db.models import Model
from django.forms import model_to_dict


def rec_model_to_dict(model: Model) -> Dict[str, Any]:
    """Recursively apply model to dict."""
    new_dict = model_to_dict(model, exclude=())
    for key, value in new_dict.items():
        if isinstance(getattr(model, key), Model):
            new_dict[key] = rec_model_to_dict(getattr(model, key))
        if isinstance(value, list) and len(value) > 0:
            if isinstance(value[0], Model):
                new_dict[key] = [
                    rec_model_to_dict(item) for item in value
                ]
    return new_dict
