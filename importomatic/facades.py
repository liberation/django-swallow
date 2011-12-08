from lxml import etree
import json


class BaseFacade(object):

    @property
    def instance_filters(self):
        raise NotImplemented()


class XmlFacade(BaseFacade):
    """Xml file wrapper to access it's properties passed to
    :meth:`DefaultConfig.populate`"""

    def __init__(self, item, path):
        self.item = item
        self.path = path

    @classmethod
    def items(cls, file_path, f):
        xml = etree.parse(f)
        root = xml.getroot()
        return [cls(root, file_path)]

    def __getattribute__(self, attribute):
        try:
            return super(XmlFacade, self).__getattribute__(attribute)
        except AttributeError:
            return self.item.find(attribute)

    def __str__(self):
        return '<%s %s>' % (type(self).__name__, self.path)


class JsonFacade(BaseFacade):

    def __init__(self, file_path, content, item):
        super(JsonFacade, self).__init__(file_path, content)
        self.item
