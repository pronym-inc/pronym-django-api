from django.forms import Form, ModelForm

from .exceptions import ApiValidationError


class ValidatorMixin:
    def validate(self):
        return self.is_valid()


class NullValidator(ValidatorMixin):
    def __init__(self, data, *args, **kwargs):
        self.cleaned_data = data

    def is_valid(self):
        return True


class Validator(NullValidator):
    def __init__(self, data, *args, **kwargs):  # pragma: no cover
        self.data = data


class FormValidator(ValidatorMixin, Form):
    pass


class PassedPkValidator(Validator):
    """
    ModelFormValidators use child validators to handle relationships
    with other database objects.  These can be specified either as
    JSON objects, in which case they go through their own
    ModelFormValidator, or they can be specified as an integer, representing
    a primary key.  This validator is used to track the latter, and contains
    the logic for validating the object exists.
    """
    @classmethod
    def for_model(cls, model_):
        class MyPassedPkValidator(cls):
            model = model_

        return MyPassedPkValidator

    def __init__(self, pk):
        self.pk = pk

    def is_valid(self):
        try:
            self._get_instance()
        except self.model.DoesNotExist:
            self.errors = ["Could not find model."]
            return False
        return True

    def save(self):
        return self._get_instance()

    def _get_instance(self):
        return self.model.objects.get(pk=self.pk)


def make_patch_validator(validator_cls):
    class PatchValidator(validator_cls):
        def __init__(self, *args, **kwargs):
            validator_cls.__init__(self, *args, **kwargs)
            # Make all fields optional.
            for field in self.fields.values():
                field.required = False

    return PatchValidator


class ModelFormValidator(ValidatorMixin, ModelForm):
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
            o2o_fields=[],
            patch_mode=False
    ):
        class MyModelFormValidator(cls):
            many_to_many_fields = m2m_fields
            one_to_many_fields = o2m_fields
            many_to_one_fields = m2o_fields
            one_to_one_fields = o2o_fields
            _patch_mode = patch_mode

            class Meta:
                model = model_
                exclude = []

        return MyModelFormValidator

    def __init__(self, *args, **kwargs):
        ModelForm.__init__(self, *args, **kwargs)
        self._m2m_validators = {}
        self._o2m_validators = {}
        self._m2o_validators = {}
        self._o2o_validators = {}

    def clean(self):
        cleaned_data = ModelForm.clean(self)

        relationship_errors = {}
        for m2m_field in self.many_to_many_fields:
            field_errors = []
            validator_class = m2m_field['validator']
            pk_validator_class = PassedPkValidator.for_model(
                validator_class.Meta.model)
            name = m2m_field['name']
            if self._patch_mode and name not in self.data:
                continue
            for idx, item in enumerate(self.data.get(name, [])):
                if isinstance(item, int) or isinstance(item, str):
                    validator = pk_validator_class(item)
                else:
                    validator = validator_class(item)
                if not validator.is_valid():
                    field_errors.append(
                        {"index": idx, "errors": validator.errors}
                    )
                else:
                    self._m2m_validators.setdefault(name, [])
                    self._m2m_validators[name].append(validator)
            if field_errors:
                relationship_errors[name] = field_errors

        for o2m_field in self.one_to_many_fields:
            field_errors = []
            validator_class = o2m_field['validator']
            name = o2m_field['name']
            if self._patch_mode and name not in self.data:
                continue
            for idx, item in enumerate(self.data.get(name, [])):
                validator = validator_class(item)
                if not validator.is_valid():
                    field_errors.append({
                        "index": idx,
                        "errors": validator.errors
                    })
                else:
                    self._o2m_validators.setdefault(name, [])
                    self._o2m_validators[name].append(validator)
            if field_errors:
                relationship_errors[name] = field_errors

        for m2o_field in self.many_to_one_fields:
            validator_class = m2o_field['validator']
            pk_validator_class = PassedPkValidator.for_model(
                validator_class.Meta.model)
            name = m2o_field['name']
            if self._patch_mode and name not in self.data:
                continue
            item = self.data.get(name, {})
            if isinstance(item, int) or isinstance(item, str):
                validator = pk_validator_class(item)
            else:
                validator = validator_class(item)
            if not validator.is_valid():
                relationship_errors[name] = validator.errors
            else:
                self._m2o_validators[name] = validator

        for o2o_field in self.one_to_one_fields:
            validator_class = o2o_field['validator']
            if self._patch_mode:
                validator_class = make_patch_validator(validator_class)
            name = o2o_field['name']
            if self._patch_mode and name not in self.data:
                continue
            item = self.data.get(name, {})
            validator = validator_class(item)
            if not validator.is_valid():
                relationship_errors[name] = validator.errors
            else:
                self._o2o_validators[name] = validator

        if len(relationship_errors) > 0:
            raise ApiValidationError(relationship_errors)

        return cleaned_data

    def patch(self, obj):
        self._save_m2o_fields(obj)
        self._save_o2o_fields(obj)

        for field_name, value in self.cleaned_data.items():
            if field_name in self.data:
                setattr(obj, field_name, value)

        obj.save()

        self._save_m2m_fields(obj)
        self._save_o2m_fields(obj)

        return obj

    def save(self, commit=True):
        obj = ModelForm.save(self, commit=False)

        self._save_m2o_fields(obj)
        self._save_o2o_fields(obj)

        if commit:
            obj.save()

        self._save_m2m_fields(obj)
        self._save_o2m_fields(obj)

        return obj

    def _save_m2m_fields(self, obj):
        for field_name, validators in self._m2m_validators.items():
            objs = list(map(
                lambda validator: validator.save(),
                validators
            ))
            m2m_manager = getattr(obj, field_name)
            m2m_manager.set(objs)

    def _save_m2o_fields(self, obj):
        m2o_fields = {
            field_name: validator.save()
            for field_name, validator
            in self._m2o_validators.items()
        }
        for field_name, val in m2o_fields.items():
            setattr(obj, field_name, val)

    def _save_o2m_fields(self, obj):
        for field_name, validators in self._o2m_validators.items():
            # Find the related field name
            rel_name = getattr(self.Meta.model, field_name).field.name

            for validator in validators:
                o2m_obj = validator.save(commit=False)
                setattr(o2m_obj, rel_name, obj)
                o2m_obj.save()

    def _save_o2o_fields(self, obj):
        o2o_fields = {
            field_name: validator.save()
            for field_name, validator
            in self._o2o_validators.items()
        }

        for field_name, val in o2o_fields.items():
            setattr(obj, field_name, val)
