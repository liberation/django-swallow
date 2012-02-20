import os
import re

from base import BaseSwallowTests

try:
    from django.test.utils import override_settings
except ImportError:
    from override_settings import override_settings

from . import Article
from integration import ArticleMapper
from integration import ArticlePopulator
from integration import ArticleBuilder
from integration import ArticleConfig
from integration import setup_matchings_and_sections

class TransactionsTests(BaseSwallowTests):

    def test_rollback_one_to_one(self):
        """Tests that if a one to one affectation fails
        the transaction rolled back and that other instances
        are properly saved"""

        setup_matchings_and_sections()

        class ArticleMapperFailsOnOneMapper(ArticleMapper):

            @property
            def title(self):
                title = self._item.find('title').text
                if title  == 'Article Ski':
                    raise Exception('custom exception')
                return title

        class BuilderFailsOnOneMapper(ArticleBuilder):

            Mapper = ArticleMapperFailsOnOneMapper
            Model = Article
            Populator = ArticlePopulator

        class ConfigFailsOnOneMapper(ArticleConfig):

            def load_builder(self, partial_file_path, fd):
                filename = os.path.basename(partial_file_path)
                if re.match(r'^\w+\.xml$', filename) is not None:
                    return BuilderFailsOnOneMapper(partial_file_path, fd, self)
                return None

        with override_settings(SWALLOW_DIRECTORY=self.SWALLOW_DIRECTORY):
            config = ConfigFailsOnOneMapper()
            config.run()

            # There is only two articles that made it, no more and *no less*
            self.assertEqual(2, Article.objects.count())

            # Check that the article in db are the one we expect
            for article in Article.objects.all():
                self.assertIn(article.title, ['Article Boxe', 'Article Bilboquet'])

            # check that there is the xml file for Article is in error
            error = config.error_dir()
            d = os.listdir(error)
            self.assertEqual(1, len(d))
            self.assertEqual('ski.xml', d[0])
