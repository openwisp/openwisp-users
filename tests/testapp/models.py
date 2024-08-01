from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from openwisp_users.mixins import OrgMixin, ShareableOrgMixin
from openwisp_utils.base import TimeStampedEditableModel


class Template(ShareableOrgMixin):
    name = models.CharField(max_length=16)

    def __str__(self):
        return self.name

    def clean(self):
        self._validate_org_reverse_relation('config_set')


class Config(OrgMixin):
    name = models.CharField(max_length=16)
    template = models.ForeignKey(
        Template, blank=True, null=True, on_delete=models.CASCADE
    )

    def clean(self):
        self._validate_org_relation('template')


class Tag(ShareableOrgMixin):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Shelf(ShareableOrgMixin, TimeStampedEditableModel):
    name = models.CharField(_('name'), max_length=64)
    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        abstract = False

    def clean(self):
        if self.name == "Intentional_Test_Fail":
            raise ValidationError('Intentional_Test_Fail')
        return self


class Book(OrgMixin, TimeStampedEditableModel):
    name = models.CharField(_('name'), max_length=64)
    author = models.CharField(_('author'), max_length=64)
    shelf = models.ForeignKey(
        'testapp.Shelf', on_delete=models.CASCADE, blank=True, null=True
    )

    def __str__(self):
        return self.name

    class Meta:
        abstract = False


class Library(models.Model):
    name = models.CharField(_('name'), max_length=64)
    address = models.TextField(null=True, blank=True)
    book = models.ForeignKey('testapp.Book', on_delete=models.CASCADE)

    def __str__(self):
        return self.name
