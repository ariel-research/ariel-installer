from django.apps import AppConfig


class UtilsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'utils'

    def ready(self):
        from utils.jobs.scheduler import AITasksScheduler
        tasks_scheduler = AITasksScheduler()
        tasks_scheduler.check_new_commits()
        tasks_scheduler.check_running_projects()
