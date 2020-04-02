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


class ListSerializer(Serializer):
    entry_serializer_class = None
    result_key = 'results'

    @classmethod
    def for_serializer(cls, serializer_class):
        class MyListSerializer(cls):
            entry_serializer_class = serializer_class

        return MyListSerializer

    def serialize(self):
        return {
            self.result_key: list(map(
                lambda item: self.entry_serializer_class(
                    self.view, self.validator, item).serialize(),
                self.processing_artifact
            ))
        }
