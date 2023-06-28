from __future__ import unicode_literals

__author__ = 'David Baum'

import os

from django.http import Http404, HttpResponse
from django.views import View

from github.models import AIGitHubProject
from github.utils import AIApplicationRunner


class AIProjectAccessLogFileReadView(View):
    content_type_value = 'text/plain'
    model = AIGitHubProject

    def get(self, request, project_id):
        try:
            instance = self.model.objects.get(pk=project_id)
            access_logs_path = AIApplicationRunner(instance).access_log_path
            if os.path.exists(access_logs_path):
                with open(access_logs_path, 'r') as f:
                    file_data = f.read()
                    response = HttpResponse(
                        file_data,
                        content_type=self.content_type_value
                    )
                    response['Content-Disposition'] = 'inline; filename=' + os.path.basename(access_logs_path)
                    return response
            else:
                raise Http404
        except self.model.DoesNotExist:
            raise Http404


class AIProjectErrorLogFileReadView(View):
    content_type_value = 'text/plain'
    model = AIGitHubProject

    def get(self, request, project_id):
        try:
            instance = self.model.objects.get(pk=project_id)
            error_log_path = AIApplicationRunner(instance).error_log_path
            if os.path.exists(error_log_path):
                with open(error_log_path, 'r') as f:
                    file_data = f.read()
                    response = HttpResponse(
                        file_data,
                        content_type=self.content_type_value
                    )
                    response['Content-Disposition'] = 'inline; filename=' + os.path.basename(error_log_path)
                    return response
            else:
                raise Http404
        except self.model.DoesNotExist:
            raise Http404
