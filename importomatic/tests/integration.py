import os, shutil

from lxml import etree

from django.test import TestCase
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management import call_command

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

    @property
    def title(self):
        return self.item.find('title').text

    @property
    def source(self):
        return self.item.find('source').text

    @property
    def weight(self):
        return self.item.find('weight').text

    @property
    def section(self):
        return self.item.find('section').text


class ArticlePopulator(BasePopulator):

    _one_to_one = ['title']
    _always_update = ['title']
    _update_if_object_not_modified = ['kind']

    def _item_is_modified(self, facade, instance):
        return instance.publication_date == instance.update_date

    def sources(self, facade, instance):
        self.populate_from_matching(
            'SOURCES',
            facade,
            instance,
            'kind'
        )

    def sections(self, facade, instance):
        self.populate_from_matching(
            'SECTIONS',
            facade,
            instance,
            'sections',
            create_through=self.create_article_to_section,
            get_or_create_related=self.get_or_create_section_from_name,
        )

    def primary_section(sef, facade, instance):
       self.populate_from_matching(
            'SECTIONS',
            facade,
            instance,
            'primary_sections',
            first_matching=True,
            get_or_create_related=self.get_or_create_section_from_name,
        )


class ArticleConfig(DefaultConfig):

    model = Article
    Facade = ArticleFacade
    Populator = ArticlePopulator

    def match(self, f):
        return f.endswith('.xml') and not f.startswith('.')

    @staticmethod
    def get_or_create_section_from_name(facade, instance, value):
        section, created = Section.objects.get_or_create(name=value)
        section.save()
        return section, created

    @staticmethod
    def create_article_to_section(section, article, facade):
        through = ArticleToSection(
            article=article,
            section=section,
            weight=facade.weight,
        )
        through.save()
        return through


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

    def _test_article_created(self):
        self.assertEqual(3, Article.objects.count())
        expected_values = {
            'Article Ski': {
                'kind':'DEPECHE',
                'sections': ['SPORT', 'SPORT INDIVIDUEL', 'SPORT DE GLISSE'],
                'weight': 10,
                'primary_section': 'SPORT',
            },
            'Article Boxe': {
                'kind':'DEPECHE',
                'sections': ['SPORT', 'SPORT INDIVIDUEL'],
                'weight': 20, 
                'primary_section': 'SPORT',
            },
            'Article Bilboquet': {
                'kind':'ARTICLE',
                'sections': ['SPORT'],
                'weight': 30,
                'primary_section': 'SPORT',
            },
        }

        for article in Article.objects.all():
            self.assertIn(article.title, expected_values.keys())
            expected_value = expected_values[article.title]
            self.assertEqual(expected_value['kind'], article.kind)
            self.assertEqual(
                len(expected_value['sections']),
                article.sections.count()
            )
            for section in article.sections.all():
                self.assertIn(section.name, expected_value['sections'])

            self.assertEqual(1, article.primary_sections.count())

            self.assertEqual(
                expected_value['primary_section'],
                article.primary_sections.all()[0].name
            )

            # check that get_or_create works
            self.assertEqual(3, Section.objects.count())

    def test_run_without_command(self):
        """Tests full configuration without command"""
        config = ArticleConfig()
        config.run()

        self._test_article_created()

    def test_run_with_command(self):
        """Tests full configuration with command"""
        call_command(
            'importomatic',
            'importomatic.tests.integration.ArticleConfig'
        )

        self._test_article_created()
