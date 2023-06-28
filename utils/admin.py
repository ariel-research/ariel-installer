from __future__ import unicode_literals

__author__ = 'David Baum'

from django.contrib import admin, messages
from django.contrib.admin.utils import model_ngettext
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.views.decorators.csrf import csrf_protect


from safedelete.admin import SafeDeleteAdmin
from safedelete.models import HARD_DELETE

csrf_protect_m = method_decorator(csrf_protect)


class SafeDeleteAdminExtended(SafeDeleteAdmin):
    hard_delete_template = "admin/hard_delete_selected_confirmation.html"
    actions = ('undelete_selected', 'hard_delete_selected',)

    def hard_delete_selected(self, request, queryset):
        """ Admin action to delete objects finally. """
        if not self.has_delete_permission(request):
            raise PermissionDenied

        original_queryset = queryset.all()
        queryset = queryset.filter(deleted__isnull=False)

        if request.POST.get('post'):
            requested = original_queryset.count()
            changed = queryset.count()

            if changed:
                for obj in queryset:
                    obj.delete(force_policy=HARD_DELETE)
                if requested > changed:
                    self.message_user(
                        request,
                        "Successfully hard deleted %(count_changed)d of the "
                        "%(count_requested)d selected %(items)s." % {
                            "count_requested": requested,
                            "count_changed": changed,
                            "items": model_ngettext(self.opts, requested)
                        },
                        messages.WARNING,
                    )
                else:
                    self.message_user(
                        request,
                        "Successfully hard deleted %(count)d %(items)s." % {
                            "count": changed,
                            "items": model_ngettext(self.opts, requested)
                        },
                        messages.SUCCESS,
                    )
            else:
                self.message_user(
                    request,
                    "No permission for hard delete. Execute soft delete first.",
                    messages.ERROR
                )
            return None
        if queryset.count() == 0:
            self.message_user(
                request,
                "No permission for hard delete. Execute soft delete first.",
                messages.ERROR
            )
            return None

        opts = self.model._meta
        if len(original_queryset) == 1:
            objects_name = force_str(opts.verbose_name)
        else:
            objects_name = force_str(opts.verbose_name_plural)
        title = "Are you sure?"

        deletable_objects, model_count, perms_needed, protected = self.get_deleted_objects(queryset, request)

        context = {
            'title': title,
            'objects_name': objects_name,
            'queryset': queryset,
            'original_queryset': original_queryset,
            'opts': opts,
            'app_label': opts.app_label,
            'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
            'model_count': dict(model_count).items(),
            'deletable_objects': [deletable_objects],
            'perms_lacking': perms_needed,
            'protected': protected,
            'media': self.media,
        }

        return TemplateResponse(
            request,
            self.hard_delete_template,
            context,
        )

    hard_delete_selected.short_description = "Hard delete selected %(verbose_name_plural)s."