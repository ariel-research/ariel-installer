from __future__ import unicode_literals

__author__ = 'David Baum'

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from github.fields import GitURLField
from github.utils import RepoTools, AIApplicationRunner


class AIGitHubProject(models.Model):
    name = models.CharField(max_length=50, verbose_name=_("Project name"), db_index=True)
    url = GitURLField(max_length=255, verbose_name=_("URL"), unique=True)
    description = models.CharField(max_length=1024, blank=True, null=True, verbose_name=_("Description"))
    use_deploy_key = models.BooleanField(default=False,
                                         help_text=_('Installer SSH key is added to the repository as a deploy key')
                                         )
    port = models.PositiveIntegerField(
        _('Project port'),
        unique=True,
        validators=[MinValueValidator(1000), MaxValueValidator(9999)]
    )
    ssh_key = models.TextField(_('SSH Private Key'), default=None, blank=True, null=True)
    ssh_key_passphrase = models.TextField(_('SSH Private Key Passphrase'), default=None, blank=True, null=True)
    ssh_pubkey = models.TextField(_('SSH Public Key'), default=None, blank=True, null=True)
    git_username = models.CharField(_('Git username'), max_length=255, unique=False, blank=True, null=True)
    git_password = models.CharField(_('Git password'), max_length=128, blank=True, null=True)
    last_commit = models.CharField(_('Last commit'), max_length=255, blank=True, null=True)
    last_error = models.TextField(null=True, blank=True, help_text=_("Last processing task error"))

    class Meta:
        verbose_name_plural = _("Projects")
        verbose_name = _("Project")

    def __str__(self):
        return "%s" % self.name

    def clean(self):
        self.is_cleaned = True
        self.last_error = None
        is_already_running = AIApplicationRunner(self).is_application_running()
        if is_already_running:
            raise ValidationError(f"Another process is already running on the port {self.port}")

        repo_tools = RepoTools(project=self)
        repo_tools.pygit2_clone_repo()

        if self.last_error:
            raise ValidationError(f"An error occurred while cloning the project: {self.last_error}")
        super(AIGitHubProject, self).clean()

    def save(self, *args, **kwargs):
        if not self.is_cleaned:
            self.full_clean()
        super(AIGitHubProject, self).save(*args, **kwargs)
