import os

from sneak.query import ListQueryResult

from django.conf import settings

from sneak.query import ListQueryResult

from models import FileSystemElement, SwallowConfiguration


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
            path = settings.SWALLOW_DIRECTORY
        else:
            self.directory = directory
            path = os.path.join(settings.SWALLOW_DIRECTORY, directory)

        for f in os.listdir(path):
            full_path = os.path.join(path, f)
            relative_path = full_path[len(settings.SWALLOW_DIRECTORY) + 1:]
            fs.append(FileSystemElement(relative_path))

        return QueryResult(fs)


class SwallowConfigurationQuerySet(ListQueryResult):

    def filter(self, *args, **kwargs):
        configurations = []
        for configuration in settings.SWALLOW_CONFIGURATIONS:
            configurations.append(SwallowConfiguration(configuration))
        return QueryResult(configurations)
