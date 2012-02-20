from lxml import etree
import json


class BaseMapper(object):

    def __init__(self, item, path=None):
        self._item = item
        self._path = path

    @property
    def _instance_filters(self):
        """Should return a dictionnary used to get or create
        a new model instance"""
        raise NotImplemented()


class XmlMapper(BaseMapper):
    """Xml file mapper to access it's properties passed to
    :meth:`BaseConfig.populate`"""

    @classmethod
    def _iter_mappers(cls, builder):
        """The builder should have a fd property"""
        xml = etree.parse(builder.fd)
        root = xml.getroot()
        return [cls(root, builder.content)]

    def __str__(self):
        return '<%s %s>' % (type(self).__name__, self._path)
