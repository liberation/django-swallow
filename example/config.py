from lxml import etree

from swallow.config import BaseConfig
from swallow.mappers import BaseMapper
from swallow.populator import BasePopulator
from swallow.builder import BaseBuilder

from example.models import FeedItem


NS = {'n':'http://www.w3.org/2005/Atom'}


class FeedBuilder(BaseBuilder):

    Model = FeedItem

    class Mapper(BaseMapper):

        def __init__(self, item):
            self.item = item

        @classmethod
        def _iter_mappers(cls, file_path, f):
            xml = etree.parse(f)
            root = xml.getroot()
            for item in root.xpath('.//n:entry', namespaces=NS):
                yield cls(item)

        @property
        def _instance_filters(self):
            return {'title': self.title}

        @property
        def title(self):
            return self.item.xpath('.//n:title', namespaces=NS)[0].text[:255]

        @property
        def content(self):
            return self.item.xpath('.//n:content', namespaces=NS)[0].text

    class Populator(BasePopulator):

        _fields_one_to_one = ('title', 'content')
        _fields_if_instance_already_exists = None
        _fields_if_instance_modified_from_last_import = None

    def instance_is_locally_modified(self, instance):
        return False

    def skip(self, mapper):
        return False


class Github(BaseConfig):

    def load_builder(self, path, f):
        if path.endswith('.atom'):
            return FeedBuilder(path, f, self)
