from util import log_exception, logger

from django.db.models.fields import AutoField


class BaseBuilder(object):

    @property
    def Wrapper(self):
        raise NotImplementedError()

    @property
    def Model(self):
        raise NotImplementedError()

    @property
    def Populator(self):
        raise NotImplementedError()

    def instance_is_modified(self, instance):
        raise NotImplementedError()

    def skip(self, wrapper):
        raise NotImplementedError()

    def process_and_save(self):
        instances = []
        for wrapper in self.Wrapper._iter_wrappers(self.path, self.fd):
            if not self.skip(wrapper):
                instance = self.__get_or_create(wrapper)
                instances.append(instance)
                modified = self.instance_is_modified(instance)
                populator = self.Populator(wrapper, instance, modified)
                for field in instance._meta.fields:
                    if isinstance(field, AutoField):
                        # can't set auto field
                        pass
                    else:
                        if populator._to_set(field.name):
                            self.__set_field_name(
                                instance,
                                populator,
                                wrapper,
                                field.name
                            )
                # save to be able to populate m2m fields
                instance.save()

                # populate m2m fields
                for field in instance._meta.many_to_many:
                    if populator._to_set(field.name):
                        # m2m are always populated by populator methods
                        method = getattr(populator, field.name, None)
                        if method is not None:
                            # reset m2m
                            f = getattr(instance, field.name)
                            f.clear()  # XXX: add a hook to overide this behaviour
                            method()
                        # else ``method`` is not set no need to set this field
            # that's all folks :)
        return instances

    def __init__(self, path, fd):
        self.path = path
        self.fd = fd

    def __set_field_name(self, instance, populator, wrapper, field_name):
        if field_name in populator._fields_one_to_one:
            # it's a wrapper property
            value = getattr(wrapper, field_name)
            setattr(instance, field_name, value)
        else:
            # it may be a populator method
            method = getattr(populator, field_name, None)
            if method is not None:
                method()  # CHECKME: This doesn't return a value so
                          # that both populator methods type (m2m & property)
                          # work the same way, that said it makes
                          # creating methods for property settings complex
                          # in simple cases
            # else this field doesn't need to be populated

    def __get_or_create(self, wrapper):
        # get or create without saving
        try:
            instance = self.Model.objects.get(
                **wrapper._instance_filters
            )
        except self.Model.DoesNotExist:
            instance = self.Model(**wrapper._instance_filters)
        return instance
