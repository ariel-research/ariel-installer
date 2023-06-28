from __future__ import unicode_literals

__author__ = 'David Baum'

from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django_admin_relation_links import AdminChangeLinksMixin

from hijack.contrib.admin import HijackUserAdminMixin
from rangefilter.filter import DateRangeFilter
from safedelete.admin import highlight_deleted

from utils.admin import SafeDeleteAdminExtended
from .forms import AIUserCreationForm
from .models import AIUser


@admin.register(AIUser)
class AIUserAdmin(SafeDeleteAdminExtended, AdminChangeLinksMixin, HijackUserAdminMixin, UserAdmin):
    """EmailUser Admin model."""

    fieldsets = (
        (
            None, {
                'fields': (
                    'email', 'password', 'username', 'full_name', 'company', 'job_title',
                    'referral', 'description', 'uuid', 'date_created', 'date_modified',
                )
            }
        ),
        (
            _('Permissions'),
            {
                'fields': ('is_pending_deletion', 'is_active', 'is_staff', 'is_superuser',
                           'groups', 'user_permissions')
            }
        ),
        (
            _('Important dates'),
            {
                'fields': (
                    'last_login', 'date_joined'
                )
            }
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('email', 'password1', 'password2',)
            }
        ),
    )
    list_per_page = 25
    # The forms to add and change user instances
    add_form = AIUserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = (
                       highlight_deleted, 'get_user', 'username',
                       'is_pending_deletion', 'is_staff', 'date_joined',
                       'date_created', 'date_modified', 'last_login',
                       'company', 'uuid',
                   ) + SafeDeleteAdminExtended.list_display
    list_filter = (
                      'is_pending_deletion', 'is_staff', 'is_superuser', 'is_active', 'groups',
                      ('date_joined', DateRangeFilter), ('last_login', DateRangeFilter),
                      ('date_created', DateRangeFilter), ('date_modified', DateRangeFilter),
                  ) + SafeDeleteAdminExtended.list_filter
    search_fields = ('email', 'full_name', 'company',)
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)
    readonly_fields = (
        'uuid', 'date_created', 'date_modified',
    )
    actions = SafeDeleteAdminExtended.actions
    hijack_success_url = settings.HIJACK_LOGOUT_REDIRECT_URL

    def get_form(self, request, obj=None, **kwargs):
        kwargs['widgets'] = {'description': forms.Textarea}
        return super().get_form(request, obj, **kwargs)

    def get_user(self, obj):
        if obj.email:
            return u"%s" % obj.email
        return u"%s" % obj.username

    get_user.short_description = _('User')
