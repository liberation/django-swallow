from lxml import etree
import json


class BaseMapper(object):

    @property
    def _instance_filters(self):
        """Should return a dictionnary used to get or create
        a new model instance"""
        raise NotImplemented()


class XmlMapper(BaseMapper):
    """Xml file mapper to access it's properties passed to
    :meth:`DefaultConfig.populate`"""

    def __init__(self, item, path):
        self._item = item
        self._path = path

    @classmethod
    def _iter_mappers(cls, file_path, f):
        xml = etree.parse(f)
        root = xml.getroot()
        return [cls(root, file_path)]

    def __str__(self):
        return '<%s %s>' % (type(self).__name__, self._path)
