import os, shutil, copy

from lxml import etree

from django.test import TestCase
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.db.models import Count

from importomatic.config import DefaultConfig
from importomatic.facades import XmlFacade
from importomatic.populator import BasePopulator
from importomatic.models import Matching
from importomatic.tests import Section, Article, ArticleToSection


CURRENT_PATH = os.path.dirname(__file__)


class ArticleFacade(XmlFacade):

    @property
    def instance_filters(self):
        return {'title': self.title}


class ArticlePopulator(BasePopulator):

    _fields_one_to_one = ('title', 'author')
    _fields_if_instance_already_exists = (
        'sections',
        'primary_sections'
        'kind',
        'author',
    )
    _fields_if_instance_modified_from_last_import = (
        'sections',
        'primary_sections',
    )


    def kind(self):
        self._from_matching(
            'SOURCES',
            'kind'
        )

    def sections(self):
        self._from_matching(
            'SECTIONS',
            'sections',
            create_through=self.create_article_to_section,
            get_or_create_related=self.get_or_create_section_from_name,
        )

    def primary_sections(self):
        self._from_matching(
            'SECTIONS',
            'primary_sections',
            first_matching=True,
            get_or_create_related=self.get_or_create_section_from_name,
        )

    def get_or_create_section_from_name(self, name):
        section, created = Section.objects.get_or_create(name=name)
        return section, created

    def create_article_to_section(self, section):
        weight = self._facade.weight
        through = ArticleToSection(
            article=self._instance,
            section=section,
            weight=self._facade.weight,
        )
        through.save()
        return through


class ArticleConfig(DefaultConfig):

    model = Article
    Facade = ArticleFacade
    Populator = ArticlePopulator

    def match(self, f):
        return f.endswith('.xml') and not f.startswith('.')

    def instance_is_modified(self, instance):
        return instance.modified_by != 'importomatic'


expected_values_initial = {
    'Article Ski': {
        'kind':'DEPECHE',
        'sections': ['SPORT', 'SPORT INDIVIDUEL', 'SPORT DE GLISSE'],
        'weight': 10,
        'primary_section': 'SPORT',
        'author': 'MrFoo',
    },
    'Article Boxe': {
        'kind':'DEPECHE',
        'sections': ['SPORT', 'SPORT INDIVIDUEL'],
        'weight': 20, 
        'primary_section': 'SPORT',
        'author': 'MrFoo',
    },
    'Article Bilboquet': {
        'kind':'ARTICLE',
        'sections': ['SPORT'],
        'weight': 30,
        'primary_section': 'SPORT',
        'author': 'MrFoo',
    },
}

expected_values_after_update = copy.deepcopy(expected_values_initial)
expected_values_after_update['Article Ski']['weight'] = 100
expected_values_after_update['Article Ski']['author'] = 'MrF'
expected_values_after_update['Article Boxe']['weight'] = 200
expected_values_after_update['Article Boxe']['author'] = 'MrF'
expected_values_after_update['Article Bilboquet']['weight'] = 300
expected_values_after_update['Article Bilboquet']['author'] = 'MrF'
expected_values_after_update['Article Bilboquet']['sections'] = ['FUN']


class IntegrationTests(TestCase):

    def setUp(cls):
        import_dir = os.path.join(CURRENT_PATH, 'import')
        if os.path.exists(import_dir):
            shutil.rmtree(import_dir)
        import_bak = os.path.join(CURRENT_PATH, 'import.bak')
        shutil.copytree(import_bak, import_dir)

        settings.MEDIA_ROOT = '/tmp'
        settings.IMPORTOMATIC_DIRECTORY = os.path.join(CURRENT_PATH, 'import')
        matching = Matching(name='SECTIONS')
        f = open(os.path.join(CURRENT_PATH, 'sections.xml'))
        content = f.read()
        f.close()
        matching.file.save(
            'importomatic/sections.xml',
            ContentFile(content),
            save=True
        )

        matching = Matching(name='SOURCES')
        f = open(os.path.join(CURRENT_PATH, 'sources.xml'))
        content = f.read()
        f.close()
        matching.file.save(
            'importomatic/sources.xml',
            ContentFile(content),
            save=True
        )

    def _test_article_created(self, expected_values):
        self.assertEqual(3, Article.objects.count())

        for article in Article.objects.all():
            self.assertIn(article.title, expected_values.keys())

            # expected value for this article
            expected_value = expected_values[article.title]

            # check kind
            self.assertEqual(expected_value['kind'], article.kind)

            # check author
            self.assertEqual(expected_value['author'], article.author)

            # check weight
            for through in article.articletosection_set.all():
                self.assertEqual(expected_value['weight'], through.weight)

            # check sections
            self.assertEqual(
                len(expected_value['sections']),
                article.sections.count()
            )


            for section in article.sections.all():
                self.assertIn(section.name, expected_value['sections'])

            # check primary sections
            self.assertEqual(1, article.primary_sections.count())

            self.assertEqual(
                expected_value['primary_section'],
                article.primary_sections.all()[0].name
            )

        self._test_no_multiple_insert_of_sections()

    def _test_no_multiple_insert_of_sections(self):
        aggregates = Section.objects.values('name').annotate(count=Count('name'))
        for aggregate in aggregates:
            self.assertEqual(1, aggregate['count'])

    def _update_imports(self):
        # simulate an update
        import_dir = os.path.join(CURRENT_PATH, 'import')
        shutil.rmtree(import_dir)
        import_update = os.path.join(CURRENT_PATH, 'import.update')
        shutil.copytree(import_update, import_dir)

    def test_run_without_command(self):
        """Tests full configuration without command"""
        config = ArticleConfig()
        config.run()

        self._test_article_created(expected_values_initial)

    def test_run_with_update(self):
        config = ArticleConfig()
        # first import
        config.run()

        self._update_imports()

        # second import
        config.run()

        self._test_article_created(expected_values_after_update)

    def test_run_with_command(self):
        """Tests full configuration with command"""
        call_command(
            'importomatic',
            'importomatic.tests.integration.ArticleConfig'
        )

        self._test_article_created(expected_values_initial)
