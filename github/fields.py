from __future__ import unicode_literals

__author__ = 'David Baum'

from django.core import validators
from django.db import models
from django.forms.fields import URLField as FormURLField


class GitURLFormField(FormURLField):
    '''The repository must be accessible over http://, https://, ssh:// or git://.'''
    default_validators = [validators.URLValidator(schemes=['http', 'https', 'ssh', 'git'])]

class GitURLField(models.URLField):
    '''The repository must be accessible over http://, https://, ssh:// or git://.'''
    default_validators = [validators.URLValidator(schemes=['http', 'https', 'ssh', 'git'])]

    def formfield(self, **kwargs):
        return super(GitURLField, self).formfield(**{
            'form_class': GitURLFormField,
        })
