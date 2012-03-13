from django.test import TestCase

from swallow.builder import BaseBuilder


class PopulatorNotImplementedErrorsTests(TestCase):
    """BasePopulator has certains attributes that should be overriden check
    that these methods and properties raise a NotImplementedError exception"""

    def test_mapper(self):
        builder = BaseBuilder(None, None)
        self.assertRaises(NotImplementedError, lambda : builder.Mapper)

    def test_model(self):
        builder = BaseBuilder(None, None)
        self.assertRaises(NotImplementedError, lambda : builder.Model)

    def test_populator(self):
        builder = BaseBuilder(None, None)
        self.assertRaises(NotImplementedError, lambda : builder.Populator)

    def test_instance_is_locally_modified(self):
        builder = BaseBuilder(None, None)
        self.assertRaises(
            NotImplementedError,
            builder.instance_is_locally_modified,
            None
        )

    def test_skip(self):
        builder = BaseBuilder(None, None)
        self.assertRaises(
            NotImplementedError,
            builder.skip,
            None
        )
