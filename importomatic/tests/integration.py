import os, shutil

from django.test import TestCase
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management import call_command

from importomatic.config import DefaultConfig
from importomatic.facades import XmlFacade

from importomatic.models import Matching
from importomatic.tests import Section, Article, ArticleToSection, Author

CURRENT_PATH = os.path.dirname(__file__)



class ArticleFacade(XmlFacade):

    @property
    def instance_filters(self):
        return {'title': self.title}

    @property
    def title(self):
        return self.xml.find('//title').text

    @property
    def source(self):
        return self.xml.find('//source').text

    @property
    def weight(self):
        return self.xml.find('//weight').text

    @property
    def section(self):
        return self.xml.find('//section').text


class ArticleConfig(DefaultConfig):

    model = Article

    Facade = ArticleFacade

    def match(self, f):
        return True

    @staticmethod
    def get_or_create_section_from_title(facade, instance, value):
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

    def process(self, facade, instance):
        self.populate_from_matching(
            'SECTIONS',
            facade,
            instance,
            'sections',
            create_through=self.create_article_to_section,
            get_or_create_related=self.get_or_create_section_from_title
        )

        self.populate_from_matching(
            'SOURCES',
            facade,
            instance,
            'type'
        )

        instance.title = facade.title
        instance.save()


class IntegrationTests(TestCase):


    def setUp(cls):
        import_dir = os.path.join(CURRENT_PATH, 'import')
        if os.path.exists(import_dir):
            shutil.rmtree(import_dir)
        import_bak = os.path.join(CURRENT_PATH, 'import.bak')
        shutil.copytree(import_bak, import_dir)


        settings.MEDIA_ROOT = '/tmp'
        settings.IMPORTOMATIC_DIR = os.path.join(CURRENT_PATH, 'import')

        call_command('syncdb')

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
            'Article Foo': {
                'type':'DEPECHE',
                'sections': ['FOO', 'FOOBAR', 'FOOBARBAZ'],
                'weight': 10
            },
            'Article FooBar': {
                'type':'DEPECHE',
                'sections': ['FOOBAR', 'FOOBARBAZ'],
                'weight': 20
            },
            'Article FooBarBaz': {
                'type':'DEPECHE',
                'sections': ['FOOBARBAZ'],
                'weight': 30
            },

        }
        for article in Article.objects.all():
            self.assertIn(article.title, expected_values.keys())
            expected_value = expected_values[article.title]
            self.assertEqual(expected_value['type'], article.type)
            self.assertEqual(
                len(expected_value['sections']),
                article.sections.count()
            )
            for section in article.sections.all():
                self.assertIn(section.name, expected_value['sections'])

    def test_run_without_command(self):
        """Tests full configuration without command"""
        config = ArticleConfig()
        config.run()

        self._test_article_created()

    def test_run_with_command(self):
        call_command(
            'importomatic',
            'importomatic.tests.integration.ArticleConfig'
        )

        self._test_article_created()
