from importomatic.config import DefaultConfig
from importomatic.facades import XmlFacade

from example.models import Copy


class AtomConfigFacade(XmlFacade):

    @property
    def instance_filters(self):
        return {'title': self.path}


class Github(DefaultConfig):

    def match(self, file_path):
        return file_path.endswith('.atom')

    model = Copy

    Facade = AtomConfigFacade

    def process(self, facade, instance):
        return
