from models import Matching

from django.db.models.fields.related import ManyToManyField


class BasePopulator(object):
    """Class used by :class:`swallow.config.BaseConfig`
    to populate instance for each item. This class is meant to
    be inherited.

    The simplest ``Populator`` class you can implement is the following:

      .. code-block:: python

        class Populator(BasePopulator):

            _fields_one_to_one = ('some', 'attributes', 'found', 'in', 'mapper')
            _fields_if_instance_already_exists = None
            _fields_if_instance_modified_from_last_import = None

    This class will threat creation, update and update of modified instance
    the same way by populating every field with the value set in the mapper.
    """


    def __init__(self, mapper, instance, modified, config):
        self._mapper = mapper
        self._instance = instance
        self._modified = modified
        self._updating = False if instance.id is None else True
        self._config = config

    @property
    def _fields_one_to_one(self):
        """Fields listed here will be set directly from mapper

        This property should always be set.

        If ``_fields_one_to_one = ['foo']`` then ``instance.foo`` will be
        equal to ``mapper.foo``.

        Set to ``None`` if you want all the fields to be updated."""
        raise NotImplementedError()

    @property
    def _fields_if_instance_already_exists(self):
        """If instance already exists when processing an item
        only these fields will be updated.

        This property should always be set.

        Set to ``None`` if you want all the fields to be updated.
        """
        raise NotImplementedError()

    @property
    def _fields_if_instance_modified_from_last_import(self):
        """When processing an item, if instance already exists
        and has been modified from last import only these fields will
        be updated.

        This property should always be set.

        Set to ``None`` if you want all the fields to be updated.
        """
        raise NotImplementedError()

    def _to_set(self, field_name):
        """Compute whether the field should be set"""
        if self._updating:
            if not self._modified:
                if self._fields_if_instance_already_exists is None:
                    return True
                if field_name in self._fields_if_instance_already_exists:
                    return True
            else:
                if self._fields_if_instance_modified_from_last_import is None:
                    return True
                if field_name in self._fields_if_instance_modified_from_last_import:
                    return True
        else:
            return True
        return False
