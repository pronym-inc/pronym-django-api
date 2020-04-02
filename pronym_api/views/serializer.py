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
    many_to_many_fields = []
    one_to_many_fields = []
    many_to_one_fields = []
    one_to_one_fields = []

    @classmethod
    def for_model(
            cls,
            model_,
            m2m_fields=[],
            o2m_fields=[],
            m2o_fields=[],
            o2o_fields=[]
    ):
        class MyModelSerializer(cls):
            model = model_
            many_to_many_fields = m2m_fields
            one_to_many_fields = o2m_fields
            many_to_one_fields = m2o_fields
            one_to_one_fields = o2o_fields

        return MyModelSerializer

    def serialize(self):
        obj = self.processing_artifact
        output = model_to_dict(obj)
        for m2m_field in self.many_to_many_fields:
            field_name = m2m_field['name']
            manager = getattr(obj, field_name)
            serializer_class = m2m_field['serializer']
            output[field_name] = []
            for item in manager.all():
                serializer = serializer_class(
                    self.view, self.validator, item)
                output[field_name].append(serializer.serialize())

        for o2m_field in self.one_to_many_fields:
            field_name = o2m_field['name']
            manager = getattr(obj, field_name)
            serializer_class = o2m_field['serializer']
            output[field_name] = []
            for item in manager.all():
                serializer = serializer_class(
                    self.view, self.validator, item)
                output[field_name].append(serializer.serialize())

        for m2o_field in self.many_to_one_fields:
            field_name = m2o_field['name']
            serializer_class = m2o_field['serializer']
            item = getattr(obj, field_name)
            serializer = serializer_class(self.view, self.validator, item)
            output[field_name] = serializer.serialize()

        for o2o_field in self.one_to_one_fields:
            field_name = o2o_field['name']
            serializer_class = o2o_field['serializer']
            item = getattr(obj, field_name)
            serializer = serializer_class(self.view, self.validator, item)
            output[field_name] = serializer.serialize()

        return output


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
