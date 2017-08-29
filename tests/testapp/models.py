from django.db import models
from openwisp_users.mixins import OrgMixin, ShareableOrgMixin


class Template(ShareableOrgMixin):
    name = models.CharField(max_length=16)


class Config(OrgMixin):
    name = models.CharField(max_length=16)
    template = models.ForeignKey(Template, blank=True, null=True)

    def clean(self):
        self._validate_org_relation('template')
