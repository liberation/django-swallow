# -*- coding: utf-8 -*-
from collections import namedtuple

from django.core.files.base import ContentFile
from django.test import TestCase
from django.conf import settings

from swallow.models import Matching


xml = """
<maps>
  <map>
    <column>FOOBARBAZ</column>
    <set>
       <title>foo</title>
       <title>bar</title>
       <suptitle>baz</suptitle>
    </set>
    <set>
       <suptitle loose-compare="yes">éèçàæœ et voilà</suptitle>
    </set>
  </map>
  <map>
    <column>FOOBARBAZ2</column>
    <set>
       <title>foo</title>
       <suptitle>baz</suptitle>
    </set>
  </map>
  <map>
    <column>BAR</column>
    <set>
       <title>bar</title>
    </set>
  </map>
  <map>
    <column>FOO</column>
    <set>
       <title>foo</title>
    </set>
  </map>
  <map>
    <column>BAZ</column>
    <set>
       <title>baz</title>
    </set>
  </map>
</maps>"""


DummyFacade = namedtuple('DummyFacade', ('title', 'suptitle'))


class MatchingTests(TestCase):

    @classmethod
    def setUpClass(cls):
        settings.MEDIA_ROOT = '/tmp'

        matching = Matching(name='TEST')
        matching.file.save(
            'swallow_matchings/test.xml',
            ContentFile(xml),
            save=True
        )
        cls.matching = matching

    def test_match_1(self):
        facade = DummyFacade('foo', 'baz')
        value = self.matching.match(facade)
        self.assertEqual(['FOOBARBAZ', 'FOOBARBAZ2', 'FOO'], value)

    def test_match_2(self):
        facade = DummyFacade('foo', 'nothing')
        value = self.matching.match(facade)
        self.assertEqual(['FOO'], value)

    def test_match_3(self):
        facade = DummyFacade('bar', 'nothing')
        value = self.matching.match(facade)
        self.assertEqual(['BAR'], value)

    def test_match_loose(self):
        facade = DummyFacade('nothing', u'éèçàæœ et voilà')
        value = self.matching.match(facade)
        self.assertEqual(['FOOBARBAZ'], value)
