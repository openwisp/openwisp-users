from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Config, Template


class TestModels(TestCase):
    def test_derived_model_config(self):
        self.assertEqual(Template.objects.count(), 0)
        t = Template(name='test')
        t.full_clean()
        t.save()
        self.assertEqual(Template.objects.count(), 1)

    def test_derived_model_template(self):
        c = Config(name='test')
        with self.assertRaises(ValidationError):
            c.full_clean()
