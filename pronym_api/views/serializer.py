from django.forms.models import model_to_dict


class Serializer:
    def __init__(self, view, validator, processing_artifact):
        self.view = view
        self.validator = validator
        self.processing_artifact = processing_artifact

    def serialize(self):
        return {}


class NullSerializer(Serializer):
    pass


class ModelSerializer(Serializer):
    def serialize(self):
        return model_to_dict(self.processing_artifact)
