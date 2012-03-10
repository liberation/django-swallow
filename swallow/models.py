# -*- coding: utf-8 -*-

import os
import time
import functools

from lxml import etree

from django.db import models
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify


def normalize(string):
    return slugify(string.lower())


class Matching(models.Model):
    """Represents a matching file. A matching file is an xml file (really)
    that let you build matching rules for your
    :class:`swallow.mappers.BaseMapper` class used in ``process``
    through :meth:`swallow.config.BaseConfig.populate_from_matching`

    See also :meth:`swallow.models.Matching.match`.

    An example matching xml file follow:

      .. code-block: xml

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
    rules. Each elements of a set should have the name of a mapper
    property. Each of them is a rule, they are ANDed to form the set-rule.
    If several element inside a set have the same name, they are ORed togethe
    before being ANDed as rules of the set.
    For instance the first set in the example matching file generate a code
    equivalent to:

      .. code-block: python

        (mapper.title == "foo" or mapper.title == "bar") and mapper.suptitle == "baz"

    See also :meth:`swallow.models.Matching.match`.
    """

    # :param name: name of the matching
    name = models.CharField(max_length=250, unique=True, db_index=True)

    # :param file: file which holds the values which computes the matching
    file = models.FileField(upload_to='swallow_matchings')

    def __unicode__(self):
        return self.name

    class from_matching(object):
        """Populator method decorator that inject in the decorated method the
        result of the match modulo the result of ``post_process_match``
        callback"""

        def __init__(
                self, matching_name,
                first_match=False,
                post_process_match=None
            ):
            self.matching_name = matching_name
            self.first_match = first_match
            self.post_process_match = post_process_match

        def __call__(self, func):
            this = self

            @functools.wraps(func)
            def wrapper(self):
                matching = Matching.objects.get(name=this.matching_name)
                match = matching.match(self._mapper, this.first_match)
                if this.post_process_match is not None:
                    match = this.post_process_match(match)
                values = func(self, match)
                return values
            return wrapper

    def match(self, mapper, first_match=False):
        """Returns values or the first value if ``first_match`` is
        set that matches the mapper according the matching xml file.
        """
        # FIXME: first_match should not be used anymore
        self.file.open()
        xml = etree.parse(self.file)
        self.file.close()

        output = []  # holds values to be returned
                     # only used if ``first_match`` is ``False``

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
                    # Do not consider XML comments <!-- like this -->
                    if isinstance(rule, etree._Comment):
                        continue
                    name = rule.tag
                    loose = rule.get('loose-compare')
                    if loose == 'yes':
                        loose = True
                    else:
                        loose = False
                    v1 = rule.text
                    v2 = getattr(mapper, name)
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
                    if first_match:
                        return column

                    matched_set = True
                    break  # no need to try another set
            if matched_set:
                output.append(column)
        if not output:
            default = dict(xml.getroot().items()).get('default', None)
            if default is not None:
                if first_match:
                    return default
                else:
                    output.append(default)
        return output


class VirtualFileSystemElement(models.Model):
    """Handles virtual directory which might be a representation of
    a file/directory found on the filesystem"""

    class Meta:
            permissions = (
                ("reset_filesystemelement", "Reset a file to be run again by configuration"),
            )

    def __init__(self, name, path=None):
        # if path is None it's a pure virtual element
        # self.pk will be name
        super(VirtualFileSystemElement, self).__init__(name)
        self.path = path
        if path is not None:
            (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(path)
            self._creation_date = time.ctime(ctime)
            self._modification_date = time.ctime(mtime)
        else:
            self._creation_date = ''
            self._modification_date = ''

    def creation_date(self):
        return self._creation_date

    def modification_date(self):
        return self._modification_date

    def is_dir(self):
        if self.path is None:
            return False
        return os.path.isdir(self.path)

    def name(self):
        if (self.is_dir()
            or (self.path is None)):  # if it's a virtual directory
            html = '<a href="?directory=%s">' % self.pk
            html += '%s</a>' % self.pk
        else:
            html = '<span><a>'
            html += '%s</a></span>' % self.pk
        return html
    name.allow_tags = True


class SwallowConfiguration(models.Model):

    def __init__(self, configuration):
        # pk is a configuration class
        super(SwallowConfiguration, self).__init__(configuration)
        self.input_count = len(os.listdir(configuration.input_dir()))
        self.error_count = len(os.listdir(configuration.error_dir()))
        self.done_count = len(os.listdir(configuration.done_dir()))

    def name(self):
        name = self.pk.__name__
        admin_url = reverse(
            'admin:%s_%s_changelist' % (
                'swallow',
                'virtualfilesystemelement'
            ),
        )
        s = '<a href="%s?directory=%s">%s</a>'
        s = s % (admin_url, name, name)
        return s
    name.allow_tags = True

    def input(self):
        return self.input_count

    def done(self):
        return self.done_count

    def error(self):
        return self.error_count

    def status(self):
        return self.error_count == 0
    status.boolean = True
