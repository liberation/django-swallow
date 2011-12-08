import json


class BaseFacade(object):

    @property
    def instance_filters(self):
        raise NotImplemented()

    def __init__(self, file_path, content):
        self.content = content
        self.path = file_path


class XmlFacade(BaseFacade):
    """Xml file wrapper to access it's properties passed to
    :meth:`DefaultConfig.populate`"""

    def __init__(self, file_path, content, item):
        super(XmlFacade, self).__init__(file_path, content)
        self.item = item


class JsonFacade(BaseFacade):

    def __init__(self, file_path, content, item):
        super(JsonFacade, self).__init__(file_path, content)
        self.item
