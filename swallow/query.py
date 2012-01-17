import os

from sneak.query import ListQueryResult

from django.conf import settings
from django.utils.importlib import import_module

from sneak.query import ListQueryResult

from models import FileSystemElement, SwallowConfiguration
from config import DefaultConfig


# list configurations classes
CONFIGURATIONS = {}
for configuration_module in settings.SWALLOW_CONFIGURATION_MODULES:
    modules = import_module(configuration_module)
    for cls in vars(modules).values():

        if (isinstance(cls, type)
            and issubclass(cls, DefaultConfig)
            and cls is not DefaultConfig):
            CONFIGURATIONS[cls.__name__] = cls


class QueryResult(ListQueryResult):
    def filter(self, *args, **kwargs):
        return self._clone()

    def order_by(self, *args, **kwargs):
        return self

    def delete(self):
        return len(self.value)


class FileSystemQuerySet(ListQueryResult):

    def filter(self, *args, **kwargs):
        directory = kwargs.get('directory', None)
        if directory is None:
            directory = getattr(self, 'directory', None)

        fs = []

        if directory is None:
            self.directory = None
            for name in CONFIGURATIONS.keys():
                fs.append(FileSystemElement(name))
        else:
            self.directory = directory
            path_components = os.path.split(directory)

            # if the path is something like "foobarbaz"
            # the first componenent is an empty string
            if not path_components[0]:
                path_components = path_components[1:]
            configuration_name = path_components[0]

            path_components = path_components[1:]

            if len(path_components) == 0:
                for path in ['input', 'work', 'done', 'error']:
                    f = os.path.join(configuration_name, path)
                    fs.append(FileSystemElement(f))
            else:
                swallow_directory = path_components[0]
                path_components = path_components[1:]
                configuration = CONFIGURATIONS[configuration_name]
                path = getattr(configuration, '%s_dir' % swallow_directory)()
                path = os.path.join(path, *path_components)
                for f in os.listdir(path):
                    fs.append(FileSystemElement(f))
        return QueryResult(fs)


class SwallowConfigurationQuerySet(ListQueryResult):

    def filter(self, *args, **kwargs):
        configurations = []
        for configuration in CONFIGURATIONS.values():
            configurations.append(SwallowConfiguration(configuration))
        return QueryResult(configurations)
