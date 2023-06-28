from __future__ import unicode_literals

__author__ = 'David Baum'

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from github.models import AIGitHubProject
from github.utils import RepoTools


@receiver(pre_delete, sender=AIGitHubProject)
def log_deleted_question(sender, instance, using, **kwargs):
    repo_tools = RepoTools(instance)
    repo_tools.delete_repo()
