# -*- coding: utf-8 -*-
from collections import namedtuple

from django.core.files.base import ContentFile
from django.test import TestCase
from django.conf import settings

from swallow.models import Matching


xml = """
<maps default="DEFAULT">
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


DummyMapper = namedtuple('DummyMapper', ('title', 'suptitle'))


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
        mapper = DummyMapper('foo', 'baz')
        value = self.matching.match(mapper)
        self.assertEqual(['FOOBARBAZ', 'FOOBARBAZ2', 'FOO'], value)

    def test_match_2(self):
        mapper = DummyMapper('foo', 'nothing')
        value = self.matching.match(mapper)
        self.assertEqual(['FOO'], value)

    def test_match_3(self):
        mapper = DummyMapper('bar', 'nothing')
        value = self.matching.match(mapper)
        self.assertEqual(['BAR'], value)

    def test_match_loose(self):
        mapper = DummyMapper('nothing', u'éèçàæœ et voilà')
        value = self.matching.match(mapper)
        self.assertEqual(['FOOBARBAZ'], value)

    def test_match_default(self):
        mapper = DummyMapper('random', u'thing')
        value = self.matching.match(mapper)
        self.assertEqual(['DEFAULT'], value)

    def test_match_default_frist_match(self):
        mapper = DummyMapper('random', u'thing')
        value = self.matching.match(mapper, first_match=True)
        self.assertEqual('DEFAULT', value)
