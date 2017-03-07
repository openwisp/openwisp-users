from django.db import models

from openwisp_users.mixins import OrgMixin, ShareableOrgMixin


class Template(ShareableOrgMixin):
    name = models.CharField(max_length=16)


class Config(OrgMixin):
    name = models.CharField(max_length=16)
