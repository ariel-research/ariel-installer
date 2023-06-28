from __future__ import unicode_literals

__author__ = 'David Baum'

from django.db import models
from django.utils.translation import gettext_lazy as _


class AIAbstractDateHistoryModel(models.Model):
    date_created = models.DateTimeField(verbose_name=_("Date created"), auto_now_add=True, editable=False)
    date_modified = models.DateTimeField(verbose_name=_("Date modified"), auto_now=True, editable=False)

    class Meta:
        abstract = True
