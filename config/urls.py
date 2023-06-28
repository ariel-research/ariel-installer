from __future__ import unicode_literals

__author__ = 'David Baum'

"""
URL configuration for arielinstaller project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include

from hijack import urls as hijack_urls
from github import urls as github_urls
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('hijack/', include(hijack_urls, namespace='hijack')),
    path('github/', include(github_urls, namespace="github")),
    path('django-rq/', include('django_rq.urls'))
] + staticfiles_urlpatterns()

admin.site.site_header = settings.PROJECT_TITLE
