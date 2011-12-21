import os
import shutil

from . import Article
from integration import ArticleConfig

from swallow.config import DefaultConfig
from swallow.wrappers import XmlWrapper
from swallow.populator import BasePopulator

from django.test import TestCase
from django.conf import settings

CURRENT_PATH = os.path.dirname(__file__)

# Implement a Builder class to make this work
# Class ConfigTests(TestCase):

#     def setUp(self):
#         settings.SWALLOW_DIRECTORY = os.path.join(CURRENT_PATH, 'import')

#         self.import_dir = os.path.join(CURRENT_PATH, 'import')
#         if os.path.exists(self.import_dir):
#             shutil.rmtree(self.import_dir)
#         import_bak = os.path.join(CURRENT_PATH, 'import.bak')
#         shutil.copytree(import_bak, self.import_dir)

#     def tearDown(self):
#         shutil.rmtree(self.import_dir)

#     def test_dry_run(self):
#         """Test that dryrun doesn't create new instance and
#         that input files are not moves"""
#         class ArticleConfig(DefaultConfig):

#             model =  Article
#             Wrapper = XmlWrapper
#             Populator = None

#             def skip(self, wrapper):
#                 return True

#             def match(self, f):
#                 return True

#             def instance_is_modified(self, instance):
#                 return False

#         config = ArticleConfig(dryrun=True)
#         config.run()

#         content = os.listdir(config.input_dir)

#         self.assertEqual(3, len(content))
#         self.assertIn('ski.xml', content)
#         self.assertIn('boxe.xml', content)
#         self.assertIn('bilboquet.xml', content)
#         self.assertEqual(0, Article.objects.count())

#     def test_skip(self):
#         """Test that if tests returns ``True`` the instance creation is
#         skipped"""

#         class SkipWrapper(XmlWrapper):
#             title = 'foo'

#             @property
#             def instance_filters(self):
#                 return {'title': self.item.text}

#             @classmethod
#             def items(cls, path, f):
#                 root = super(SkipWrapper, cls).items(path, f)[0]
#                 for item in root.item.iterfind('item'):
#                     yield cls(item, path)

#             kind = 'kind'
#             title = 'title'
#             author = 'author'
#             modified_by = 'modified_by'

#         class SkipPopulator(BasePopulator):
#             _fields_one_to_one = (
#                 'title',
#                 'kind',
#                 'author',
#                 'modified_by',
#             )
#             _fields_if_instance_already_exists = []
#             _fields_if_instance_modified_from_last_import = []

#         class SkipConfig(DefaultConfig):
#             Wrapper = SkipWrapper
#             model = Article
#             Populator = SkipPopulator

#             def instance_is_modified(self, instance):
#                 return False

#             def skip(self, wrapper):
#                 return wrapper.item.text in ('1', '2')

#             def match(self, path):
#                 return True

#         config = SkipConfig()
#         config.run()

#         self.assertEqual(2, Article.objects.count())
