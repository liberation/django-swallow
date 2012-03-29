import logging
from functools import wraps
from contextlib import contextmanager

from django.db.models.fields import AutoField
from django.db import DatabaseError

from swallow.exception import StopConfig, StopBuilder, StopMapper
from swallow.util import format_exception


log = logging.getLogger('swallow.builder')


@contextmanager
def dummy():
    """Dummy context manager used when the current builder is nested,
    and does not need to handle transaction since it handled by a parent
    builder.

    Dummy context manager inside another builder process_and_save
    call most likely through a call to :function:`swallow.builder.from_builder`.
    """
    yield


class BaseBuilder(object):
    """Base class for a builder object.

    This is *must* be inherited and properly configured to work. See
    each attribute for more information how to set up this class."""

    @property
    def Mapper(self):
        """Mapper used to populate one to one fields in
        :class:`swallow.populator.Populator`.
        """
        raise NotImplementedError()

    @property
    def Model(self):
        """Django Model class to instantiate and populate."""
        raise NotImplementedError()

    @property
    def Populator(self):
        """Class that knows how to populate a model instance
        :class:`swallow.populator.Populator`.
        """
        raise NotImplementedError()

    def instance_is_locally_modified(self, instance):
        """Should return a boolean. Used to know whether the instance
        was modified locally or not. Swallow use this value to know
        if it should or not populate the instance
        """
        raise NotImplementedError()

    def skip(self, mapper):
        """Should return a boolean. Used to know whether to use this mapper
        to create/update an instance.
        """
        raise NotImplementedError()

    def process_and_save(self):
        """Builds :class:`swallow.mappers.BaseMapper` classes, instantiate
        models and populate them with the help of a populator.

        if ``managed``` is set to ``False`` the function won't try to commit
        transaction.
        """
        instances = []
        unhandled_errors = False

        for mapper in self.Mapper._iter_mappers(self):
            try:
                instance = self.process_mapper(mapper)
            except StopBuilder, e:
                # Implementor has asked to totally stop the import
                msg = u"Import of builder %s has been stopped" % self
                log_message = format_exception(e, msg)
                log.warning(log_message)
                # FIXME: empty instances?
                break
            except StopConfig:
                raise  # Propagate stop order to Config
            except StopMapper, e:
                msg = u"Import of mapper %s has been stopped" % mapper
                log_message = format_exception(e, msg)
                log.warning(log_message)
                continue  # To next mapper
            except DatabaseError, e:
                unhandled_errors = True
                msg = u"DatabaseError exception on %s" % mapper
                log_message = format_exception(e, msg)
                log.error(log_message)
                continue  # To next mapper
            except Exception, e:
                unhandled_errors = True
                msg = u"Unhandled exception on %s" % mapper
                log_message = format_exception(e, msg)
                log.error(log_message)
                continue  # To next mapper
            else:
                if instance:
                    # Instance is None if mapper has be skipped in skip method
                    instances.append(instance)
        return instances, unhandled_errors

    def process_mapper(self, mapper):
        log.info('processing of %s mapper starts' % mapper)
        if not self.skip(mapper):
            instance = self.get_or_create_instance(mapper)
            modified = self.instance_is_locally_modified(instance)
            populator = self.Populator(
                mapper,
                instance,
                modified,
                self
            )

            # --- Populate simple fields
            for field in instance._meta.fields:
                if isinstance(field, AutoField):
                    # can't set auto field
                    pass
                else:
                    if populator._to_set(field.name):
                        # Do not catch exceptions here
                        self.set_field(
                            populator,
                            instance,
                            mapper,
                            field.name
                        )

            # --- Save to be able to populate relations fields
            instance.save()

            # --- Populate m2m fields
            for field in instance._meta.many_to_many:
                if populator._to_set(field.name):
                    try:
                        self.set_m2m_field(
                            populator,
                            instance,
                            field.name
                        )
                    except (StopMapper, StopBuilder, StopConfig):
                        # Implementor has asked the import to be stopped, so
                        # propagate it
                        raise
                    except Exception, e:
                        # Unhandled error
                        # Do not stop import, just continue to next field
                        msg = u"Unhandled exception on m2m %s" % field.name
                        log_message = format_exception(e, msg)
                        log.error(log_message)
                        continue  # To next field

            # --- Populate related fields
            for related in instance._meta.get_all_related_objects():
                accessor_name = related.get_accessor_name()
                if populator._to_set(accessor_name):
                    try:
                        self.set_field(
                            populator,
                            instance,
                            mapper,
                            accessor_name
                        )
                    except (StopMapper, StopBuilder, StopConfig):
                        # Implementor has asked the import to be stopped, so
                        # propagate it
                        raise
                    except Exception, e:
                        # Unhandled error
                        # Do not stop import, just continue to next field
                        msg = u"Unhandled exception on related %s" % accessor_name
                        log_message = format_exception(e, msg)
                        log.error(log_message)
                        continue  # To next field
        else:
            log.info('skip %s mapper' % mapper)
            instance = None
        return instance

    def set_field(self, populator, instance, mapper, field_name):
#        if field_name == "original_file":
#            import ipdb; ipdb.set_trace()
        if field_name in populator._fields_one_to_one:
            # it's a mapper property
            value = getattr(mapper, field_name)
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

    def set_m2m_field(self, populator, instance, field_name):
        # m2m are always populated by populator methods
        method = getattr(populator, field_name, None)
        if method is not None:
            f = getattr(instance, field_name)
            f.clear()  # XXX: add a hook to overide
                       # this behaviour
            method()
        # else ``method`` is not set
        # no need to set this field

    def __init__(self, content, config, managed=False, parent_instance=None):
        # :param content: an open variable for content storing
        #                 it can a be file descriptor, a node in xml
        #                 document etc. Use it to store information
        #                 from where you will be able to retrieve data later
        self.content = content
        # :param config: config that runs this builder
        #                it can be the config of a parent builder
        self.config = config
        # :param managed: if the builder is in a managed transaction block
        #                 it should be set to True. If it is not managed
        #                 Then it should take care of starting and ending
        #                 transactions for each mapper.
        self.managed = managed
        # :param parent_instance: the instance created by the parent builder
        #                         you can use it in during population step
        #                         through `populator._builder.parent_instance``
        #                         /!\ Becarful it's not guaranteed that
        #                         parent_instance was already saved by the
        #                         parent builder
        self.parent_instance = parent_instance

    def get_or_create_instance(self, mapper):
        # get or create without saving
        try:
            instance = self.Model.objects.get(
                **mapper._instance_filters
            )
            log.info('fetched instance')
        except self.Model.DoesNotExist:
            instance = self.Model(**mapper._instance_filters)
            log.info('created instance')
        return instance


class from_builder(object):
    """Decorator object used to inject a builder results
    as parameters of a populator method.

    It gets the results of the related mapper property,
    create a builder for each values returned and inject
    the resulting instances as a parameter of the decorated
    populator method.
    """

    def __init__(self, BuilderClass, instance=False):
        self.BuilderClass = BuilderClass
        self.instance = instance

    def __call__(self, func):
        this = self  # this is the decorator class

        @wraps(func)
        def wrapper(self):  # self is a populator instance
            # just like it's done in BaseConfig gather created
            # instances
            instances = []
            # for each object returned by the mapper property
            # create a builder and run it
            builders_args = getattr(self._mapper, func.__name__)
            for args in builders_args:
                # Every arg here its the content parameter for the init of the
                # builder
                args = [args]
                # build builder constructor arguments
                # the inner builder inherit the config
                args.append(self._config)
                # inner builder transaction is managed by the
                # the outter builder so managed=True
                args.append(True)
                if this.instance:
                    # the caller wants the object that is currently
                    # created as argument
                    args.append(self._instance)
                builder = this.BuilderClass(*args)
                p, unhandled_errors = builder.process_and_save()
                instances.extend(p)  # FIXME: This is not consistent with
                                     # BaseConfig way of gathering created
                                     # instances
            return func(self, instances)
        return wrapper
