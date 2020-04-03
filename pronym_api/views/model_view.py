from .api_view import ApiView
from .processor import Processor, SaveValidatorProcessor
from .serializer import ListSerializer, ModelSerializer, NullSerializer
from .validator import (
    make_patch_validator, ModelFormValidator, NullValidator)


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
        return self.validator.patch(self.view.get_item())


class ModelApiView(ApiView):
    item_id_kwarg_name = 'id'

    many_to_many_fields = []
    one_to_many_fields = []
    many_to_one_fields = []
    one_to_one_fields = []

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

    def get_model_form_validator_class(self, patch_mode=False):
        return ModelFormValidator.for_model(
            self.get_model(),
            m2m_fields=self._get_relationship_fields(self.many_to_many_fields),
            o2m_fields=self._get_relationship_fields(self.one_to_many_fields),
            m2o_fields=self._get_relationship_fields(self.many_to_one_fields),
            o2o_fields=self._get_relationship_fields(self.one_to_one_fields),
            patch_mode=patch_mode
        )

    def get_model_serializer_class(self):
        return ModelSerializer.for_model(
            self.get_model(),
            m2m_fields=self._get_relationship_fields(self.many_to_many_fields),
            o2m_fields=self._get_relationship_fields(self.one_to_many_fields),
            m2o_fields=self._get_relationship_fields(self.many_to_one_fields),
            o2o_fields=self._get_relationship_fields(self.one_to_one_fields)
        )

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
        validator_cls = self.get_model_form_validator_class(
            patch_mode=True)
        return make_patch_validator(validator_cls)

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

    def _get_relationship_fields(self, in_fields):
        fields = []
        for in_field in in_fields:
            if isinstance(in_field, str):
                item = {'name': in_field}
            elif isinstance(in_field, dict):
                item = in_field
            else:  # pragma: no cover
                raise ValueError(
                    "Fields should only be specified as strings, "
                    "indicating field names, or dictionaries.")
            name = item['name']
            rel_model = getattr(self.model, name).field.related_model
            # In one to many relationships, we're actually looking for the
            # `model` attribute - we'll know if our `related_model` is
            # `self.model`.
            if rel_model == self.model:
                rel_model = getattr(self.model, name).field.model
            output = {
                'validator': ModelFormValidator.for_model(rel_model),
                'serializer': ModelSerializer.for_model(rel_model)
            }
            output.update(item)
            fields.append(output)
        return fields
