class Serializer:
    def __init__(self, view, validator, processing_artifact):
        self.view = view
        self.validator = validator
        self.processing_artifact = processing_artifact

    def serialize(self):
        return {}


class NullSerializer(Serializer):
    pass
