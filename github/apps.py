from __future__ import unicode_literals

__author__ = 'David Baum'

from django.apps import AppConfig


class GithubConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'github'

    def ready(self):
        from github import signals  # NOQA
