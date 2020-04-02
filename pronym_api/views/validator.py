from django.forms import Form, ModelForm


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


class ModelFormValidator(ValidatorMixin, ModelForm):
    @classmethod
    def for_model(cls, model_):
        class MyModelFormValidator(cls):
            class Meta:
                model = model_
                exclude = []

        return MyModelFormValidator
