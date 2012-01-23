import os

from sneak.query import ListQueryResult

from models import VirtualFileSystemElement, SwallowConfiguration
from util import get_configurations


class QueryResult(ListQueryResult):
    def filter(self, *args, **kwargs):
        return self._clone()

    def order_by(self, *args, **kwargs):
        return self

    def delete(self):
        return len(self.value)


class VirtualFileSystemQuerySet(ListQueryResult):

    def filter(self, *args, **kwargs):
        # directory in the point of view of the admin user
        # it's not the filesystem directory
        directory = kwargs.get('directory', None)
        if directory is None:
            directory = getattr(self, 'directory', None)

        fs = []

        CONFIGURATIONS = get_configurations()

        if directory is None:
            # we want to list all configurations
            self.directory = None
            for name in CONFIGURATIONS.keys():
                fs.append(VirtualFileSystemElement(name))
        else:
            # we have something like ``ConfigurationName``
            # or ``Configuration/Foo``
            self.directory = directory
            path_components = directory.split('/')

            configuration_name = path_components[0]

            # tail of the path
            path_components = path_components[1:]

            if len(path_components) == 0:
                # if path_components is empty
                # directory is something like ``{{ configuration_name }}``
                # we need to list configuration directories
                for swallow_directory in ['input', 'work', 'done', 'error']:
                    configuration = CONFIGURATIONS[configuration_name]
                    path_dir_method = getattr(
                        configuration,
                        '%s_dir' % swallow_directory
                    )
                    path = path_dir_method()
                    f = os.path.join(configuration_name, swallow_directory)
                    fs.append(VirtualFileSystemElement(f, path))
            else:
                # directory is something like
                # ``{{ configuration_name}}/{{ swallow_directory }}``
                # where ``swallow_directory`` is ``input``, ``work``
                # ``done`` or ``error``
                swallow_directory = path_components[0]
                path_components = list(path_components[1:])
                configuration = CONFIGURATIONS[configuration_name]
                path = getattr(configuration, '%s_dir' % swallow_directory)()
                path = os.path.join(path, *path_components)
                for f in os.listdir(path):
                    full_path = os.path.join(path, f)
                    name_tail = list(path_components)
                    name_tail.append(f)
                    name = os.path.join(
                        configuration_name,
                        swallow_directory,
                        *name_tail
                    )
                    fse = VirtualFileSystemElement(name, full_path)
                    fs.append(fse)
        return QueryResult(fs)


class SwallowConfigurationQuerySet(ListQueryResult):

    def filter(self, *args, **kwargs):
        CONFIGURATIONS = get_configurations()
        configurations = []
        for configuration in CONFIGURATIONS.values():
            configurations.append(SwallowConfiguration(configuration))
        return QueryResult(configurations)
