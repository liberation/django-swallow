from lxml import etree
import json


class BaseMapper(object):

    def __init__(self, content, builder=None):
        self._content = content
        self._builder = builder

    @property
    def _instance_filters(self):
        """Should return a dictionnary used to get or create
        a new model instance"""
        raise NotImplementedError()


class XmlMapper(BaseMapper):
    """Xml file mapper to access it's properties passed to
    :meth:`BaseConfig.populate`"""

    def __init__(self, item, content, builder=None):
        # content should be a path
        super(XmlMapper, self).__init__(content, builder)
        self._item = item

    @classmethod
    def _iter_mappers(cls, builder):
        # The builder should have a fd property
        xml = etree.parse(builder.fd)
        root = xml.getroot()
        yield cls(root, builder.content)

    def __str__(self):
        return '<%s %s>' % (type(self).__name__, self._content)
