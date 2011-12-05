import json
from lxml import etree


class BaseFacade(object):

    @property
    def __instance_filters__(self):
        raise NotImplemented()

    def __init__(self, path, file):
        self.file = file
        self.path = path


class XmlFacade(BaseFacade):
    """Xml file wrapper to access it's properties passed to
    :meth:`DefaultConfig.populate`"""

    def __init__(self, path, file):
        super(XmlFacade, self).__init__(path, file)
        self.xml = etree.parse(file)

    def get_value(self, node, path, nsmap):
        """Attempts to retrieve either the node text or node attribute
        specified."""
        if '@' in path:
            if path.count('@') > 1:
                msg = "You have more than one attribute accessor."
                raise ValueError(msg)
            path, attr = path.rsplit('.@')
            node = node.find(path, namespaces=nsmap)
            resolved = node.attrib.get(attr, "")
        else:
            if path == ".":
                # this will get text in an XML node, regardless of placement
                texts = [text.strip() for text in node.xpath("text()")]
                resolved = ''.join(texts)
            else:
                nval = node.find(path, namespaces=nsmap)
                resolved = nval.text if nval is not None else ""
        return resolved.strip()


class JsonFacade(BaseFacade):

    def __init__(self, path, file):
        super(JsonFacade, self).__init__(path, file)
        self.json = json.load(file)