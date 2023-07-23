from __future__ import unicode_literals

__author__ = 'David Baum'

import django_rq, logging
from datetime import datetime

from django.core.paginator import Paginator

from github.models import AIGitHubProject
from github.utils import AIApplicationRunner, RepoTools

from scheduler import job

@job
def check_new_commits_task():
    logging.info("Running checking new commits task")

    queryset = AIGitHubProject.objects.all().order_by('id')
    paginator = Paginator(queryset, 200)

    for page_number in paginator.page_range:
        page = paginator.page(page_number)

        for obj in page.object_list:
            obj.is_cleaned = True
            repo_tools = RepoTools(obj)
            repo_tools.git_fetch()


@job
def check_running_projects_task():
    logging.info("Running checking the projects are running")

    queryset = AIGitHubProject.objects.all().order_by('id')
    paginator = Paginator(queryset, 200)

    for page_number in paginator.page_range:
        page = paginator.page(page_number)

        for obj in page.object_list:
            obj.is_cleaned = True
            is_running = AIApplicationRunner(obj).is_application_running()
            if not is_running:
                AIApplicationRunner(obj).run()


class AITasksScheduler():
    def __init__(self):
        self.scheduler = django_rq.get_scheduler('low')
        for job in self.scheduler.get_jobs():
            job.delete()

    def check_new_commits(self, interval=60):  # every 60 seconds
        self.scheduler.schedule(datetime.utcnow(), check_new_commits_task, interval=interval)

    def check_running_projects(self, interval=60):  # every 60 seconds
        self.scheduler.schedule(datetime.utcnow(), check_running_projects_task, interval=interval)
