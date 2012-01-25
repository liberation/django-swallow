import os
import shutil

from . import Article
from integration import ArticleConfig

from swallow.config import DefaultConfig
from swallow.mappers import XmlMapper
from swallow.populator import BasePopulator
from swallow.builder import BaseBuilder
from swallow import settings

from django.test import TestCase

CURRENT_PATH = os.path.dirname(__file__)


class BaseSwallowTests(TestCase):

    def setUp(self):
        settings.SWALLOW_DIRECTORY = os.path.join(CURRENT_PATH, 'import')

        self.import_dir = os.path.join(CURRENT_PATH, 'import')
        if os.path.exists(self.import_dir):
            shutil.rmtree(self.import_dir)
        import_initial = os.path.join(CURRENT_PATH, 'import.initial')
        shutil.copytree(import_initial, self.import_dir)

    def tearDown(self):
        shutil.rmtree(self.import_dir)



class ConfigTests(BaseSwallowTests):

    def test_dry_run(self):
        """Test that dryrun doesn't create new instance and
        that input files are not moved"""

        class ArticleBuilder(BaseBuilder):
            pass

        class ArticleConfig(DefaultConfig):

            def load_builder(self, path, fd):
                return ArticleBuilder(path, fd)

            def instance_is_modified(self, instance):
                return False

        config = ArticleConfig(dryrun=True)
        config.run()

        content = os.listdir(config.input_dir())

        self.assertEqual(3, len(content))
        self.assertIn('ski.xml', content)
        self.assertIn('boxe.xml', content)
        self.assertIn('bilboquet.xml', content)
        self.assertEqual(0, Article.objects.count())

    def test_skip(self):
        """Test that if ``Builder.skip`` returns ``True`` the instance
        creation is skipped"""

        class SkipMapper(XmlMapper):
            title = 'foo'

            @property
            def _instance_filters(self):
                return {'title': self._item.text}

            @classmethod
            def _iter_mappers(cls, path, f):
                root = super(SkipMapper, cls)._iter_mappers(path, f)[0]
                for item in root._item.iterfind('item'):
                    yield cls(item, path)

            kind = 'kind'
            title = 'title'
            author = 'author'
            modified_by = 'modified_by'

        class SkipPopulator(BasePopulator):
            _fields_one_to_one = (
                'title',
                'kind',
                'author',
                'modified_by',
            )
            _fields_if_instance_already_exists = []
            _fields_if_instance_modified_from_last_import = []

        class SkipBuilder(BaseBuilder):

            Mapper = SkipMapper
            Model = Article
            Populator = SkipPopulator

            def skip(self, mapper):
                txt = mapper._item.text
                return txt in ('1', '2')

            def instance_is_locally_modified(self, instance):
                return False

        class SkipConfig(DefaultConfig):

            def load_builder(self, path, fd):
                return SkipBuilder(path, fd)

            def instance_is_locally_modified(self, instance):
                return False

        config = SkipConfig()
        config.run()

        self.assertEqual(2, Article.objects.count())


class PostProcessTest(BaseSwallowTests):


    class PostProcessConfig(DefaultConfig):

        def load_builder(self, path, fd):
            class PostProcessBuilder(object):

                def process_and_save(self):
                    return True

            return PostProcessBuilder()

        def instance_is_locally_modified(self, instance):
            return False

        def postprocess(self, instances):
            self.__flag__ = instances

    def test_postprocess(self):

        config = self.PostProcessConfig()
        config.run()

        self.assertTrue(hasattr(config, '__flag__'))
        self.assertTrue(isinstance(config.__flag__, list))
        self.assertEqual(3, len(config.__flag__))
        for x in config.__flag__:
            self.assertTrue(x)
