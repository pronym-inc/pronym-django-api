from django.forms import Form, ModelForm


class ValidatorMixin:
    pass


class NullValidator(ValidatorMixin):
    def __init__(self, data, *args, **kwargs):
        self.cleaned_data = data

    def is_valid(self):
        return True


class Validator(NullValidator):
    pass


class FormValidator(ValidatorMixin, Form):
    pass


class ModelFormValidator(ValidatorMixin, ModelForm):
    pass
