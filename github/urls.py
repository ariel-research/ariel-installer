from django.urls import path

from github.views import AIProjectAccessLogFileReadView, AIProjectErrorLogFileReadView

app_name = "github"
urlpatterns = [
    path("<int:project_id>/access-logs/", AIProjectAccessLogFileReadView.as_view(), name="read_access_logs"),
    path("<int:project_id>/error-logs/", AIProjectErrorLogFileReadView.as_view(), name="read_error_logs"),
]
