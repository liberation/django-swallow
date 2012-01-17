import shutil 
import os

from django.contrib import admin
from django.conf import settings
from django.contrib.admin.views.main import ChangeList

from sneak.admin import SneakAdmin

from query import FileSystemQuerySet, SwallowConfigurationQuerySet
from models import FileSystemElement, SwallowConfiguration, Matching


admin.site.register(Matching)


#
# Administration for browsing SWALLOW_DIRECTORY
#

class FileSystemChangeListView(ChangeList):

    def get_query_set(self):
        return self.root_query_set # filetering is already done by FileSystemModelAdmin


def reset(modeladmin, request, queryset):
    for path in request.POST.getlist('_selected_action'):
        full_path = os.path.join(settings.SWALLOW_DIRECTORY, path)
        path = os.path.dirname(full_path)
        path = os.path.join(path, '..', 'input')
        shutil.move(full_path, path)
reset.short_description = 'Reset'


def delete(modeladmin, request, queryset):
    for path in request.POST.getlist('_selected_action'):
        full_path = os.path.join(settings.SWALLOW_DIRECTORY, path)
        os.remove(full_path)
delete.short_description = 'Delete'


class FileSystemAdmin(SneakAdmin):
    QuerySet = FileSystemQuerySet

    list_display = ('path', 'creation_date', 'modification_date')
    actions = [reset, delete]

    def get_changelist(self, request):
        return FileSystemChangeListView

    def queryset(self, request):
        GET = request.GET.copy()
        # pop directory from querystring because later
        # the admin try to match it against a field
        directory = GET.get('directory', None)
        qs = self.QuerySet()
        qs = qs.filter(directory=directory)
        return qs

    def has_add_permission(self, request):
        return False

    def get_actions(self, request):
        """
        Override django's native get_actions to return only change list's
        actions that are allowed for current user.
        """
        actions = super(FileSystemAdmin, self).get_actions(request)
        for action in actions.keys():
            if action == u'delete_selected':
                del actions['delete_selected']
            opts = self.opts
            perm = '%s.%s_%s' % (
                opts.app_label,
                action,
                opts.object_name.lower()
            )
            if not request.user.has_perm(perm):
                del actions[action]
        return actions

if hasattr(settings, 'SWALLOW_CONFIGURATION_MODULES'):
    admin.site.register([FileSystemElement], FileSystemAdmin)


#
# Administration for browsing Swallow Configuration
#

class SwalllowConfigurationAdmin(SneakAdmin):
    QuerySet = SwallowConfigurationQuerySet

    list_display = ('name', 'input', 'done', 'error', 'goodissime',)
    actions = None

    def has_add_permission(self, request):
        return False

if hasattr(settings, 'SWALLOW_CONFIGURATION_MODULES'):
    admin.site.register([SwallowConfiguration], SwalllowConfigurationAdmin)
