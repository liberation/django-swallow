from collections import namedtuple

from django.test import TestCase

from swallow.populator import BasePopulator


MockModel = namedtuple('Model', ('id',))
MockBuilder = namedtuple('Builder', ('config',))


class PopulatorNotImplementedErrorsTests(TestCase):
    """BaseBuilder has certains attributes that should be overriden check
    that these methods and properties raise a NotImplementedError exception"""

    def test_fields_one_to_one(self):
        populator = BasePopulator(
            None,
            MockModel(None),
            None,
            MockBuilder(None)
        )
        self.assertRaises(
            NotImplementedError,
            lambda : populator._fields_one_to_one
        )

    def test_fields_if_instance_already_exists(self):
        populator = BasePopulator(
            None,
            MockModel(None),
            None,
            MockBuilder(None)
        )
        self.assertRaises(
            NotImplementedError,
            lambda : populator._fields_if_instance_already_exists)

    def test_fields_if_instance_modified_from_last_import(self):
        populator = BasePopulator(
            None,
            MockModel(None),
            None,
            MockBuilder(None)
        )
        self.assertRaises(
            NotImplementedError,
            lambda : populator._fields_if_instance_modified_from_last_import)


class PopulatorTestSetTests(TestCase):

    def test_to_set_not_updating(self):
        pass

    def test_to_set_updating_one(self):
        """Test _to_set if the populator is:
         - updating
         - modified
         and field in ``_fields_if_instance_modified_from_last_import``
         """
        pass

    def test_to_set_updating_two(self):
        """Test _to_set if the populator is:
         - updating
         - modified
         and ``_fields_if_instance_modified_from_last_import`` is None
         """
        pass

    def test_to_set_updating_three(self):
        """Test _to_set if the populator is:
         - updating
         - modified
         and ``_fields_if_instance_modified_from_last_import`` is not None
         and field not in ``_fields_if_instance_modified_from_last_import``
         """
        pass

    def test_to_set_updating_four(self):
        """Test _to_set if the populator is:
         - updating
         - not modified
         and field in ``_fields_if_instance_already_exists``
         """
        pass

    def test_to_set_updating_five(self):
        """Test _to_set if the populator is:
         - updating
         - not modified
         and ``_fields_if_instance_already_exists`` is None
         """
        pass

    def test_to_set_updating_six(self):
        """Test _to_set if the populator is:
         - updating
         - not modified
         and ``_fields_if_instance_already_exists`` is not None
         and field not in ``_fields_if_instance_already_exists``
         """
        pass
