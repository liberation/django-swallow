# -*- coding: utf-8 -*-
from lxml import etree

import translitcodec

from django.db import models


def normalize(string):
    return string.lower().encode('translit/long')


class Matching(models.Model):
    """Represents a matching file. A matching file is an xml file (really)
    that let you build matching rules for your
    :class:`importomatic.facades.BaseFacade` class used in ``process``
    through :meth:`importomatic.config.DefaultConfig.populate_from_matching`

    See also :meth:`importomatic.models.Matching.match`.

    An example matching xml file follow:

      .. highligh: xml

        <maps>
          <map>
            <column>OUTPUT</column>
            <set>
               <title>foo</title>
               <title>bar</title>
               <suptitle>baz</suptitle>
            </set>
            <set>
               <suptitle loose-compare="yes">éèçàæœ et voilà</suptitle>
            </set>
          </map>
        </maps>

    This define a list of  ``map`` elements. Each map define a value
    to be outputed as ``column`` element. If one ``set`` element is
    a match the ``column`` value should be returned. Each set defines
    rules. Each elements of a set should have the name of a facade
    property. Each of them is a rule, they are ANDed to form the set-rule.
    If several element inside a set have the same name, they are ORed togethe
    before being ANDed as rules of the set.
    For instance the first set in the example matching file generate a code
    equivalent to:

      .. highlight: python

        (facade.title == "foo" or facade.title == "bar") and facade.suptitle == "baz"

    See also :meth:`importomatic.models.Matching.match`.
    """

    # :param name: name of the matching
    name = models.CharField(max_length=250)

    # :param file: file which holds the values which computes the matching
    file = models.FileField(upload_to='importomatic')

    # :param first_matching: even if the django field is an M2M, only
    #                        populate with the first result
    first_matching = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def match(self, facade, first_matching=False):
        """Returns values or the first value if ``first_matching`` is
        set that matches the facade according the matching xml file.
        """
        first_matching = first_matching or self.first_matching

        self.file.open()
        xml = etree.parse(self.file)
        self.file.close()

        output = []  # holds values to be returned
                     # only used if ``first_matching`` is ``False``

        for map in xml.iterfind('//map'):
            # a possible return value
            column = map.find('column').text

            matched_set = False
            for set in map.iterfind('set'):
                # build the set of rules
                # set of rules is a dictionary::
                #
                #   {
                #       'title': False,
                #       'suptitle': False
                #   }
                #
                # The value of a key is True if at least
                # one rule matched
                match = dict()
                for rule in set.iterchildren():
                    name = rule.tag
                    loose = rule.get('loose-compare')
                    if loose == 'yes':
                        loose = True
                    else:
                        loose = False
                    v1 = rule.text
                    v2 = getattr(facade, name)
                    if loose:
                        v1 = normalize(v1)
                        v2 = normalize(v2)
                    if v1 == v2:
                        match[name] = True
                    else:
                        v = match.get(name, None)
                        if v is None:
                            match[name] = False
                matched = True
                for v in match.values():
                    if not v:
                        matched = False
                        break

                if matched:
                    # the set matched no need to test other set
                    # for another match one is enough
                    # if we get here the set matched so the map matched
                    if first_matching:
                        return [column]

                    matched_set = True
                    break  # no need to try another set
            if matched_set:
                output.append(column)
        return output
