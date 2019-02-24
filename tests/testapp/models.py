from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from openwisp_users.mixins import OrgMixin, ShareableOrgMixin
from openwisp_utils.base import TimeStampedEditableModel


class Template(ShareableOrgMixin):
    name = models.CharField(max_length=16)

    def clean(self):
        self._validate_org_reverse_relation('config')


class Config(OrgMixin):
    name = models.CharField(max_length=16)
    template = models.ForeignKey(Template, blank=True, null=True,
                                 on_delete=models.CASCADE)

    def clean(self):
        self._validate_org_relation('template')


class Shelf(OrgMixin, TimeStampedEditableModel):
    name = models.CharField(_('name'), max_length=64)

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
    shelf = models.ForeignKey('testapp.Shelf', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        abstract = False
