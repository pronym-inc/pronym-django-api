from django.test import TestCase

from pronym_api.views.validator import ValidatorMixin, FormValidator


class ValidatorWithContextTest(TestCase):

    def setUp(self) -> None:
        self.validator_kwargs = {
            "foo": "bar",
            "key": "two"
        }

    def test_instantiate_validator_mixin(self):
        validator_instance = ValidatorMixin(context=self.validator_kwargs)

        self.assertDictEqual(validator_instance._context, self.validator_kwargs)

    def test_instantiate_form_validator(self):
        complex_validator = FormValidator({}, context=self.validator_kwargs)

        self.assertDictEqual(
            complex_validator._context, self.validator_kwargs
        )

        self.assertTrue(hasattr(complex_validator, 'data'))
        self.assertTrue(hasattr(complex_validator, 'files'))
        self.assertTrue(hasattr(complex_validator, 'auto_id'))
        self.assertTrue(hasattr(complex_validator, 'initial'))
        self.assertTrue(hasattr(complex_validator, 'error_class'))
        self.assertTrue(hasattr(complex_validator, 'label_suffix'))
        self.assertTrue(hasattr(complex_validator, 'empty_permitted'))
        self.assertTrue(hasattr(complex_validator, '_errors'))
