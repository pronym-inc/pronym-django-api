from .api_view import ApiView
from .processor import Processor, SaveValidatorProcessor
from .serializer import ListSerializer, ModelSerializer, NullSerializer
from .validator import ModelFormValidator, NullValidator


class RetrieveRecordProcessor(Processor):
    def process(self):
        return self.view.get_item()


class SearchRecordsProcessor(Processor):
    def process(self):
        return self.view.get_collection()


class DeleteRecordByPkProcessor(Processor):
    def process(self):
        self.view.delete_item()


class PatchProcessor(Processor):
    def process(self):
        item = self.view.get_item()
        for field_name, value in self.validator.cleaned_data.items():
            if field_name in self.validator.data:
                setattr(item, field_name, value)
        item.save()
        return item


class ModelApiView(ApiView):
    item_id_kwarg_name = 'id'

    def check_resource_exists(self):
        if self.is_item_request():
            try:
                self.get_item()
            except self.model.DoesNotExist:
                return False
        return True

    def get_method_config(self):
        view_type_key = \
            'collection' if self.is_collection_request() else 'item'
        return self.get_methods()[view_type_key].get(self.request.method, {})

    def get_methods(self):
        return {
            'collection': {
                'GET': {
                    'validator': self.get_search_validator_class(),
                    'processor': self.get_search_processor_class(),
                    'serializer': self.get_search_serializer_class()
                },
                'POST': {
                    'validator': self.get_create_validator_class(),
                    'processor': self.get_create_processor_class(),
                    'serializer': self.get_create_serializer_class()
                }
            },
            'item': {
                'DELETE': {
                    'validator': self.get_delete_validator_class(),
                    'processor': self.get_delete_processor_class(),
                    'serializer': self.get_delete_serializer_class()
                },
                'GET': {
                    'validator': self.get_retrieve_validator_class(),
                    'processor': self.get_retrieve_processor_class(),
                    'serializer': self.get_retrieve_serializer_class()
                },
                'PATCH': {
                    'validator': self.get_modify_validator_class(),
                    'processor': self.get_modify_processor_class(),
                    'serializer': self.get_modify_serializer_class()
                },
                'PUT': {
                    'validator': self.get_replace_validator_class(),
                    'processor': self.get_replace_processor_class(),
                    'serializer': self.get_replace_serializer_class()
                }
            }
        }

    def delete_item(self):
        self.get_item().delete()

    def get_collection(self):
        return self.get_model().objects.all()

    def get_item(self):
        if not hasattr(self, '_item'):
            self._item = self.get_collection().get(
                pk=self.get_item_id_from_url())
        return self._item

    def get_item_id_from_url(self):
        return self.kwargs[self.item_id_kwarg_name]

    def get_model(self):
        return self.model

    def get_model_form_validator_class(self):
        return ModelFormValidator.for_model(self.get_model())

    def get_model_serializer_class(self):
        return ModelSerializer

    def get_validator_kwargs(self):
        # In the case of a PUT request, we want to pass along the object as
        # the instance.
        if self.request.method == 'PUT':
            return {'instance': self.get_item()}
        return {}

    def get_search_validator_class(self):
        return NullValidator

    def get_search_processor_class(self):
        return SearchRecordsProcessor

    def get_search_serializer_class(self):
        return ListSerializer.for_serializer(self.get_model_serializer_class())

    def get_create_validator_class(self):
        return self.get_model_form_validator_class()

    def get_create_processor_class(self):
        return SaveValidatorProcessor

    def get_create_serializer_class(self):
        return self.get_model_serializer_class()

    def get_delete_validator_class(self):
        return NullValidator

    def get_delete_processor_class(self):
        return DeleteRecordByPkProcessor

    def get_delete_serializer_class(self):
        return NullSerializer

    def get_retrieve_validator_class(self):
        return NullValidator

    def get_retrieve_processor_class(self):
        return RetrieveRecordProcessor

    def get_retrieve_serializer_class(self):
        return self.get_model_serializer_class()

    def get_modify_validator_class(self):
        validator_cls = self.get_model_form_validator_class()

        class PatchValidator(validator_cls):
            def __init__(self, *args, **kwargs):
                validator_cls.__init__(self, *args, **kwargs)
                # Make all fields optional.
                for field in self.fields.values():
                    field.required = False

        return PatchValidator

    def get_modify_processor_class(self):
        return PatchProcessor

    def get_modify_serializer_class(self):
        return self.get_model_serializer_class()

    def get_replace_validator_class(self):
        return self.get_model_form_validator_class()

    def get_replace_processor_class(self):
        return SaveValidatorProcessor

    def get_replace_serializer_class(self):
        return self.get_model_serializer_class()

    def is_collection_request(self):
        return not self.is_item_request()

    def is_item_request(self):
        return 'id' in self.kwargs
