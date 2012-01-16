from models import Matching

from django.db.models.fields.related import ManyToManyField


class BasePopulator(object):
    """Class used by :class:`importomatic.config.DefaultConfig`
    to populate instance for each item. This class is meant to
    be inherited.

    The simplest ``Populator`` class you can implement is the following:

      .. highlight:: python

        class Populator(BasePopulator):

            _fields_one_to_one = ('some', 'attributes', 'found', 'in', 'mapper')
            _fields_if_instance_already_exists = None
            _fields_if_instance_modified_from_last_import = None

    This class will threat creation, update and update of modified instance
    the same way by populating every field with the value set in the the
    facade.
    """


    def __init__(self, mapper, instance, modified):
        self._mapper = mapper
        self._instance = instance
        self._modified = modified
        self._updating = False if instance.id is None else True

    @property
    def _fields_one_to_one(self):
        """Fields listed here will be set directly from facade

        This property should always be set.

        If ``_fields_one_to_one = ['foo']`` then ``instance.foo`` will be
        equal to ``facade.foo``.

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

    def _from_matching(
            self,
            matching_name,
            field_name,
            first_matching=False,
            get_or_create_related=None,
            create_through=None,
        ):

        # exceptions are catched in ``process_recursively``
        matching = Matching.objects.get(name=matching_name)

        # fetch field for ``field_name``
        if field_name in self._instance._meta.get_all_field_names():
            field = self._instance._meta.get_field_by_name(field_name)[0]
        else:
            msg = 'field %s not found on %s.' % (field_name, self._instance)
            raise Exception(msg)

        if isinstance(field, ManyToManyField):
            # it's a M2M field
            values = matching.match(self._mapper, first_matching)
            for value in values:
                if get_or_create_related is None:
                    msg = 'Tried to set a related  property without '
                    msg += '``get_or_create_related`` provided.'
                    raise Exception(msg)
                else:
                    related, created = get_or_create_related(value)
                    if created:
                        related.save()
                    if create_through is None:
                        # let's try to add the generic M2M
                        field = getattr(self._instance, field_name)
                        field.add(related)
                    else:
                        through = create_through(
                            related,
                        )
                        through.save()
        else:
            # since it's a property we only need one value
            # force first_match
            values = matching.match(self._mapper, first_matching=True)
            setattr(self._instance, field_name, values[0])

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
