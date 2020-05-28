"""A custom model form to handle creating related objects as part of object creation."""
import logging
from typing import Optional, List, Dict, Any, TypeVar, Type, Mapping, ClassVar, Union

from django.db import models
from django.db.models import Model, OneToOneField, ForeignKey, ManyToManyField, ManyToOneRel
from django.db.models.fields.related import RelatedField
from django.db.models.fields.related_descriptors import ManyToManyDescriptor
from django.forms import ModelChoiceField, Field, ModelForm

ModelT = TypeVar("ModelT", bound=Model)


logger = logging.getLogger("pronym_api")


class LazyModelForm(ModelForm):
    """A model form which will create related objects at appropriate times."""
    _custom_form_class_for_field_name: 'ClassVar[Dict[str, Type[LazyModelForm]]]' = {}
    _pre_save_forms_or_ids: 'Dict[str, Optional[Union[LazyModelForm, int, Model]]]'
    _post_save_forms_or_ids: 'Dict[str, Optional[List[Optional[Union[LazyModelForm, int, Model]]]]]'

    __patch_mode: bool

    @classmethod
    def for_model(
            cls,
            model_: Type[Model],
            custom_form_classes: 'Optional[Dict[str, Type[LazyModelForm]]]' = None
    ) -> 'Type[LazyModelForm]':
        """Get a LazyModelForm for the given model."""
        form_classes = custom_form_classes or {}

        class MyLazyModelForm(LazyModelForm):
            """Dynamically created form."""
            _custom_form_class_for_field_name = form_classes

            class Meta:
                """Customize the model."""
                model = model_
                exclude = ()

        return MyLazyModelForm

    def __init__(self, data: Optional[Mapping[str, Any]] = None, **kwargs: Any) -> None:
        self.__patch_mode = kwargs.pop('patch_mode', False)
        super().__init__(data, **kwargs)
        # If we're in patch mode, remove fields that the user didn't specify in the request.
        if self.__patch_mode:
            patch_fields_to_remove: List[str] = []
            for patch_field_name in self.fields.keys():
                if data and patch_field_name not in data:
                    patch_fields_to_remove.append(patch_field_name)
            for patch_field in patch_fields_to_remove:
                del self.fields[patch_field]
        # Look for related fields.  Remove them and add pre-save and post-save forms as appropriate.
        self._pre_save_forms_or_ids: Dict[str, Optional[Union[LazyModelForm, int, Model]]] = {}
        self._post_save_forms_or_ids: Dict[str, List[Optional[Union[LazyModelForm, int, Model]]]] = {}
        field: Field
        fields_to_remove: List[str] = []
        for field_name, field in self.fields.items():
            if isinstance(field, ModelChoiceField):
                model = field.queryset.model
                model_field: models.Field = getattr(self.Meta.model, field_name).field
                form_cls = self._get_form_class_for_field(field_name, model)
                if isinstance(model_field, OneToOneField) or isinstance(model_field, ForeignKey):
                    payload: Optional[Union[LazyModelForm, int]]
                    if data:
                        field_val = data.get(field_name)
                        if isinstance(field_val, dict):
                            payload = form_cls(field_val or {})
                        elif isinstance(field_val, int):
                            payload = field_val
                        else:
                            payload = None
                    else:  # pragma: no cover
                        payload = form_cls()
                    fields_to_remove.append(field_name)
                    self._pre_save_forms_or_ids[field_name] = payload
                elif isinstance(model_field, ManyToManyField) or isinstance(model_field, ManyToOneRel):
                    many_payload: Optional[List[Optional[Union[LazyModelForm, int, Model]]]]
                    if data:
                        field_val = data.get(field_name)

                        if isinstance(field_val, list):
                            many_payload = []
                            for item in field_val:
                                if isinstance(item, int):
                                    many_payload.append(item)
                                elif isinstance(item, dict):
                                    many_payload.append(form_cls(item or {}))
                                else:
                                    many_payload.append(None)
                        else:
                            many_payload = None
                    else:  # pragma: no cover
                        many_payload = []
                    fields_to_remove.append(field_name)
                    self._post_save_forms_or_ids[field_name] = many_payload
        for field_name in fields_to_remove:
            del self.fields[field_name]

    def full_clean(self) -> None:
        """Clean our extra forms too."""
        super().full_clean()

        def validate_related_field(my_field_name: str, my_form_or_id: Any) -> Optional[Union[LazyModelForm, Model]]:
            """Helper function to sort out ids and forms which will be mingled together."""
            if isinstance(my_form_or_id, LazyModelForm):
                if not my_form_or_id.is_valid():
                    self._errors[my_field_name] = {
                        field_name_: [error.message for error in errors]
                        for field_name_, errors
                        in my_form_or_id.errors.as_data().items()
                    }
                return my_form_or_id
            elif isinstance(my_form_or_id, int):
                my_model = self.__get_model_for_field(my_field_name)
                if my_model:
                    try:
                        return my_model.objects.get(pk=my_form_or_id)
                    except my_model.DoesNotExist:
                        self._errors[my_field_name] = [f"Invalid id specified: {my_form_or_id}"]
                        return None
                else:  # pragma: no cover
                    raise Exception(f"Could not find suitable model for field.")
            else:
                self._errors[my_field_name] = ["Received invalid data type."]

        # Update pre-save fields first.
        updates: Dict[str, Model] = {}
        for field_name, form_or_id in self._pre_save_forms_or_ids.items():
            result = validate_related_field(field_name, form_or_id)
            if isinstance(result, Model):
                updates[field_name] = result
        self._pre_save_forms_or_ids.update(updates)
        # Now do post-save fields.
        many_updates: Dict[str, List[Union[Model, LazyModelForm, int]]] = {}
        for field_name, maybe_entries in self._post_save_forms_or_ids.items():
            if maybe_entries is None:
                self._errors[field_name] = ["Received non-array in JSON where we expected an array."]
                continue
            output: List[Union[Model, LazyModelForm, int]] = []
            for entry in maybe_entries:
                validation = validate_related_field(field_name, entry)
                if validation is not None:
                    output.append(validation)
            many_updates[field_name] = output
        self._post_save_forms_or_ids.update(many_updates)

    def save(self, commit: bool = True) -> Any:
        """Save our extra forms, too, at the appropriate times.  We will assume commit is always True."""
        if not commit:  # pragma: no cover
            raise Exception("LazyModelForm.save cannot be called with commit=False!")

        def instance_from_form_or_model(my_form_or_model: Union[LazyModelForm, int, Model]):
            """Helper function to disambiguate forms or models in our dictionaries."""
            if isinstance(my_form_or_model, LazyModelForm):
                return my_form_or_model.instance
            elif isinstance(my_form_or_model, Model):
                return my_form_or_model
            else:  # pragma: no cover
                raise Exception("Wound up with neither form nor model.  This is wrong.")

        # One to One and FKs are saved first and then just assigned to our object before it's saved.
        for field_name, form_or_model in self._pre_save_forms_or_ids.items():
            obj = instance_from_form_or_model(form_or_model)
            obj.save()
            setattr(self.instance, field_name, obj)
        # Save our actual object.
        instance = super().save(commit=True)
        # Handle M2M and things that have us as foreign key (M2O)
        for field_name, entries in self._post_save_forms_or_ids.items():
            model_field = getattr(type(instance), field_name)
            if isinstance(model_field, ManyToManyDescriptor):
                manager = getattr(instance, field_name)
                manager.clear()
            for form_or_model in entries:
                obj = instance_from_form_or_model(form_or_model)
                # Save a many to many field right away
                if isinstance(model_field, ManyToManyDescriptor):
                    obj.save()
                    manager = getattr(instance, field_name)
                    manager.add(obj)
                else: # pragma: no cover
                    logger.warning("Received an unknown *-to-many relationship.")
                    continue
        return instance

    def _get_custom_form_class_for_field(self, field_name: str) -> 'Optional[Type[LazyModelForm]]':
        """Get the form class for field.  Implement this to map subfields to specific fields."""
        return self._custom_form_class_for_field_name.get(field_name)

    def _get_default_form_class_for_field(self, model: Type[Model]) -> 'Type[LazyModelForm]':
        """Generate a custom form class for the provided field."""
        return LazyModelForm.for_model(model, self._custom_form_class_for_field_name)

    def _get_form_class_for_field(self, field_name: str, model: Type[Model]) -> 'Type[LazyModelForm]':
        """Generate the form class for the field."""
        return self._get_custom_form_class_for_field(field_name) or self._get_default_form_class_for_field(model)

    def __get_model_for_field(self, field_name: str) -> Optional[Type[Model]]:
        field = getattr(self.Meta.model, field_name).field
        if isinstance(field, RelatedField):
            return field.related_model
        return None  # pragma: no cover
