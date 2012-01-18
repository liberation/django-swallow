import shutil 
import os

from django.contrib import admin
from django.conf import settings
from django.contrib.admin.views.main import ChangeList

from sneak.admin import SneakAdmin

from query import VirtualFileSystemQuerySet, SwallowConfigurationQuerySet
from models import VirtualFileSystemElement, SwallowConfiguration, Matching
from util import CONFIGURATIONS

admin.site.register(Matching)


#
# Administration for browsing SWALLOW_DIRECTORY
#

class VirtualFileSystemChangeListView(ChangeList):

    def get_query_set(self):
        # filetering is already done by VirtualFilesystemModelAdmin
        return self.root_query_set


def get_configuration_and_swallow_path(directory):
    components = os.path.split(directory)
    configuration_name, swallow_directory, path = (
        components[0],
        components[1],
        components[2:]
    )
    configuration = CONFIGURATIONS[configuration_name]
    swallow_dir_method = getattr(configuration, '%s_dir' % swallow_directory)
    swallow_dir_path = swallow_dir_method()
    return configuration, swallow_dir_path


def reset(modeladmin, request, queryset):
    # directory should always be set
    directory = request.GET['directory']
    configuration, swallow_dir_path = get_configuration_and_swallow_path(
        directory
    )
    for path in request.POST.getlist('_selected_action'):
        full_path = os.path.join(swallow_dir_path, path)
        input_dir = configuration.input_dir()
        shutil.move(full_path, input_dir)
reset.short_description = 'Reset'


def delete(modeladmin, request, queryset):
    directory = request.GET['directory']
    configuration, swallow_dir_path = get_configuration_and_swallow_path(
        directory
    )
    for path in request.POST.getlist('_selected_action'):
        full_path = os.path.join(swallow_dir_path, path)
        os.remove(full_path)
delete.short_description = 'Delete'


class FileSystemAdmin(SneakAdmin):
    QuerySet = VirtualFileSystemQuerySet

    list_display = ('name', 'creation_date', 'modification_date')
    actions = [reset, delete]

    def get_changelist(self, request):
        return VirtualFileSystemChangeListView

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
    admin.site.register([VirtualFileSystemElement], FileSystemAdmin)


#
# Administration for browsing Swallow Configuration
#

class SwalllowConfigurationAdmin(SneakAdmin):
    QuerySet = SwallowConfigurationQuerySet

    list_display = ('name', 'status', 'input', 'done', 'error', )
    actions = None

    def has_add_permission(self, request):
        return False

if hasattr(settings, 'SWALLOW_CONFIGURATION_MODULES'):
    admin.site.register([SwallowConfiguration], SwalllowConfigurationAdmin)
