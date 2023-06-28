from __future__ import unicode_literals

__author__ = 'David Baum'

import os

from django.contrib import admin, messages
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import AIGitHubProject
from .utils import RepoTools, AIApplicationRunner


@admin.register(AIGitHubProject)
class AIGitHubProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'url', 'has_ssh_key',
                    'is_application_running', 'has_last_error', 'last_error', 'port', 'project_actions',
                    'last_commit']

    def has_last_error(self, obj) -> bool:
        if obj.last_error:
            return True
        return False

    def is_application_running(self, obj) -> bool:
        return AIApplicationRunner(obj).is_application_running()

    def git_pull_from_repo(self, request, queryset):
        queryset.update(task_id=None)
        for qs in queryset:
            repo_tools = RepoTools(project=qs)
            repo_tools.pygit2_clone_repo()
            qs.save()

    def has_ssh_key(self, obj):
        return True if obj.ssh_key else False

    def stop_application(self, request, project_id, *args, **kwargs):
        obj = self.model.objects.get(pk=project_id)
        obj.last_error = None

        runner = AIApplicationRunner(obj)
        runner.kill_application()

        if not obj.last_error:
            messages.add_message(request, messages.SUCCESS,
                                 _('The application has been successfully stopped'))
        else:
            messages.add_message(request, messages.WARNING,
                                 _('The application was not stopped'))

        meta = self.model._meta
        return HttpResponseRedirect(
            reverse(
                f"admin:{meta.app_label}_{meta.model_name}_changelist"
            )
        )

    def start_application(self, request, project_id, *args, **kwargs):
        obj = self.model.objects.get(pk=project_id)
        obj.last_error = None

        runner = AIApplicationRunner(obj)
        runner.run()

        if not obj.last_error:
            messages.add_message(request, messages.SUCCESS,
                                 _('The application has been successfully started'))
        else:
            messages.add_message(request, messages.WARNING,
                                 _('The application was not started'))

        meta = self.model._meta
        return HttpResponseRedirect(
            reverse(
                f"admin:{meta.app_label}_{meta.model_name}_changelist"
            )
        )

    def project_actions(self, obj):
        meta = self.model._meta
        is_running = self.is_application_running(obj)
        reversed_stop_url = reverse(f'admin:{meta.app_label}_{meta.model_name}_stop_application', args=[obj.pk])
        reversed_restart_url = reverse(f'admin:{meta.app_label}_{meta.model_name}_start_application', args=[obj.pk])
        reversed_download_access_logs_url = reverse(f'admin:{meta.app_label}_{meta.model_name}_download_access_logs',
                                                    args=[obj.pk])
        reversed_download_error_logs_url = reverse(f'admin:{meta.app_label}_{meta.model_name}_download_error_logs',
                                                  args=[obj.pk])
        reversed_read_access_logs_url = reverse(f'github:read_access_logs',
                                                args=[obj.pk])
        reversed_read_error_logs_url = reverse(f'github:read_error_logs',
                                                args=[obj.pk])
        buttons = [
            f'<div class="button"><a style="color: white" href="{reversed_restart_url}">{"Restart" if is_running else "Start"}</a></div><br/>',
            f'<div class="button"><a style="color: white" href="{reversed_download_access_logs_url}">Download Access Logs</a></div><br/>',
            f'<div class="button"><a style="color: white" href="{reversed_download_error_logs_url}">Download Error Logs</a></div><br/>',
            f'<div class="button"><a style="color: white" href="{reversed_read_error_logs_url}" target="_blank">Read Error Logs</a></div><br/>',
            f'<div class="button"><a style="color: white" href="{reversed_read_access_logs_url}" target="_blank">Read Access Logs</a></div><br/>'
        ]
        if is_running:
            buttons.insert(0, f'<div class="button"><a style="color: white" href="{reversed_stop_url}">{"Stop"}</a></div><br/>')
        return format_html("".join(buttons))

    def download_access_logs_file(self, request, project_id, *args, **kwargs):
        obj = self.model.objects.get(pk=project_id)
        access_logs_path = AIApplicationRunner(obj).access_log_path
        file_data = ''
        with open(access_logs_path, 'r') as f:
            file_data = f.read()

        response = HttpResponse(file_data, content_type='plain/text')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(access_logs_path)}"'
        return response

    def download_error_logs_file(self, request, project_id, *args, **kwargs):
        obj = self.model.objects.get(pk=project_id)
        error_logs_path = AIApplicationRunner(obj).error_log_path
        file_data = ''
        with open(error_logs_path, 'r') as f:
            file_data = f.read()

        response = HttpResponse(file_data, content_type='plain/text')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(error_logs_path)}"'
        return response

    def get_urls(self):
        urls = super().get_urls()
        meta = self.model._meta
        custom_urls = [
            path(
                "<int:project_id>/stop-application/",
                self.admin_site.admin_view(self.stop_application),
                name=f'{meta.app_label}_{meta.model_name}_stop_application',
            ),
            path(
                "<int:project_id>/start-application/",
                self.admin_site.admin_view(self.start_application),
                name=f'{meta.app_label}_{meta.model_name}_start_application',
            ),
            path(
                "<int:project_id>/access-logs/",
                self.admin_site.admin_view(self.download_access_logs_file),
                name=f'{meta.app_label}_{meta.model_name}_download_access_logs',
            ),
            path(
                "<int:project_id>/error-logs/",
                self.admin_site.admin_view(self.download_error_logs_file),
                name=f'{meta.app_label}_{meta.model_name}_download_error_logs',
            )
        ]
        return custom_urls + urls

    has_ssh_key.boolean = True
    has_last_error.boolean = True
    is_application_running.boolean = True
    git_pull_from_repo.short_description = _("Git pull")
    project_actions.short_description = _("Actions")
    project_actions.allow_tags = True
    actions = [git_pull_from_repo]
