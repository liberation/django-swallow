from models import Matching

from django.db.models.fields.related import ManyToManyField
from django.db.models.fields import AutoField


class BasePopulator(object):

    @property
    def _one_to_one(self):
        raise NotImplementedError()

    @property
    def _always_update(self):
        raise NotImplementedError()

    @property
    def _never_populate(self):
        raise NotImplementedError()

    @property
    def _update_if_object_not_modified(self):
        raise NotImplementedError()

    def __init__(self, facade, instance):
        self.facade = facade
        self.instance = instance

    def _modified():
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

        if field_name in self.instance._meta.get_all_field_names():
            field = self.instance._meta.get_field_by_name(field_name)[0]
        else:
            msg = 'field %s not found on %s.' % (field_name, self.instance)
            raise Exception(msg)

        if isinstance(field, ManyToManyField):
            # it's a M2M field
            values = matching.match(self.facade, first_matching)
            for value in values:
                if get_or_create_related is None:
                    msg = 'Try to set a related  property without '
                    msg += '``get_or_create_related`` provided.'
                    raise Exception(msg)
                else:
                    related, created = get_or_create_related(
                        self.facade,
                        self.instance,
                        value,
                    )
                    if created:
                        related.save()
                    if create_through is None:
                        # let's try to add the generic M2M
                        field = getattr(self.instance, field_name)
                        field.add(related)
                    else:
                        through = create_through(
                            related,
                            self.instance,
                            self.facade,
                        )
                        through.save()
        else:
            # since it's a property we only need one value
            # force first_match
            values = matching.match(self.facade, first_matching=True)
            setattr(self.instance, field_name, values[0])

    def _run(self):
        fields_to_update = list(self._always_update)

        modified = self._modified()

        if not modified:
            fields_to_update += self._update_if_object_not_modified

        for field in self.instance._meta.fields:
            if isinstance(field, AutoField):
                # can't set auto field
                continue
            else:
                # it is a property try to populate it right now
                if (field.name not in self._never_populate and
                    (not modified or field.name in fields_to_update)):
                    field_name = field.name
                    if field_name in self._one_to_one:
                        # it's a facade property
                        value = getattr(self.facade, field_name)
                        setattr(self.instance, field_name, value)
                    else:
                        # it's a populator method
                        method = getattr(self, field_name)
                        value = method()

        # save to be able to populate m2m fields
        self.instance.save()
        # populate m2m fields
        for field in self.instance._meta.many_to_many:
            if (field.name not in self._never_populate and
                (not modified or field.name in fields_to_update)):
                # m2m are always populated by populator methods
                method = getattr(self, field.name)
                method()

        # that's all folks :)
