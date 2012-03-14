import os
import shutil

try:
    from django.test.utils import override_settings
except ImportError:
    from override_settings import override_settings

from . import Article
from integration import ArticleConfig
from base import BaseSwallowTests

from swallow.config import BaseConfig
from swallow.mappers import XmlMapper
from swallow.populator import BasePopulator
from swallow.builder import BaseBuilder


CURRENT_PATH = os.path.dirname(__file__)


class ConfigTests(BaseSwallowTests):

    def test_dry_run(self):
        """Test that dryrun doesn't create new instance and
        that input files are not moved"""

        class ArticleBuilder(BaseBuilder):
            pass

        class ArticleConfig(BaseConfig):

            def load_builder(self, builder):
                return ArticleBuilder(builder, self)

            def instance_is_modified(self, instance):
                return False

        with override_settings(SWALLOW_DIRECTORY=self.SWALLOW_DIRECTORY):
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
            def _iter_mappers(cls, builder):
                mapper = super(SkipMapper, cls)._iter_mappers(builder).next()
                for item in mapper._item.iterfind('item'):
                    yield cls(item, builder.content)

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

            def __init__(self, content, config, managed=False):
                super(SkipBuilder, self).__init__(content, config, managed)
                self.fd = self.config.open(content)

            def skip(self, mapper):
                txt = mapper._item.text
                return txt in ('1', '2')

            def instance_is_locally_modified(self, instance):
                return False

        class SkipConfig(BaseConfig):

            def load_builder(self, builder):
                return SkipBuilder(builder, self)

            def instance_is_locally_modified(self, instance):
                return False

        with override_settings(SWALLOW_DIRECTORY=self.SWALLOW_DIRECTORY):
            config = SkipConfig()
            config.run()

            self.assertEqual(2, Article.objects.count())


class PostProcessTest(BaseSwallowTests):
    """Check that the postprocessing step is called when
    it exists"""

    class PostProcessConfig(BaseConfig):

        def load_builder(self, spam):
            class PostProcessBuilder(object):

                def process_and_save(self):
                    return True, False  # a dummy value and error_flag

            return PostProcessBuilder()

        def instance_is_locally_modified(self, instance):
            return False

        def postprocess(self, instances):
            self.__flag__ = instances

    def test_postprocess(self):

        with override_settings(SWALLOW_DIRECTORY=self.SWALLOW_DIRECTORY):
            config = self.PostProcessConfig()
            config.run()

            self.assertTrue(hasattr(config, '__flag__'))
            self.assertTrue(isinstance(config.__flag__, list))
            self.assertEqual(3, len(config.__flag__))
            for x in config.__flag__:
                self.assertTrue(x)
