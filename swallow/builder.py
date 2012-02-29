import logging
from functools import wraps
from contextlib import contextmanager

from util import log_exception, logger

from django.db.models.fields import AutoField
from django.db import IntegrityError
from django.db.transaction import commit_manually
from django.db.transaction import rollback
from django.db.transaction import commit


logger = logging.getLogger()


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

        # only non-managed code need to be managed
        manager = dummy if self.managed else commit_manually

        error = False
        for mapper in self.Mapper._iter_mappers(self):
            logger.info('processing of %s mapper starts' % mapper)
            if not self.skip(mapper):
                with manager():
                    current_mapper_on_error = False
                    instance = self.get_or_create_instance(mapper)
                    instances.append(instance)
                    modified = self.instance_is_locally_modified(instance)
                    populator = self.Populator(
                        mapper,
                        instance,
                        modified,
                        self.config
                    )
                    for field in instance._meta.fields:
                        if isinstance(field, AutoField):
                            # can't set auto field
                            pass
                        else:
                            if populator._to_set(field.name):
                                try:
                                    self.set_field(
                                        populator,
                                        instance,
                                        mapper,
                                        field.name
                                    )
                                except Exception, e:
                                    msg = 'exception raised during '
                                    msg += 'field population'
                                    log_exception(e, msg)
                                    current_mapper_on_error = True
                                    error = True
                    # save to be able to populate m2m fields
                    try:
                        instance.save()
                    except IntegrityError, e:
                        msg = 'exception raised during '
                        msg += 'instance save'
                        log_exception(e, msg)
                        current_mapper_on_error = True
                    # populate m2m fields
                    for field in instance._meta.many_to_many:
                        if populator._to_set(field.name):
                            try:
                                self.set_m2m_field(
                                    populator,
                                    instance,
                                    field.name
                                )
                            except Exception, e:
                                msg = 'exception raised during '
                                msg += 'm2m field population'
                                log_exception(e, msg)
                                current_mapper_on_error = True
                                error = True
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
                            except Exception, e:
                                msg = 'exception raised during '
                                msg += 'm2m field population'
                                log_exception(e, msg)
                                current_mapper_on_error = True
                                error = True
                    if current_mapper_on_error:
                        if not self.managed:
                            msg = 'ROLLBACK %s for %s' % (self, mapper)
                            logger.critical(msg)
                            rollback()
                        msg = '%s builder raised an exception ' % self
                        msg += 'in process_and_save'
                        logger.error(msg)
                    else:
                        if not self.managed:
                            logger.info('COMMIT %s' % self)
                            commit()
                        msg = 'saved %s@%s: %s' % (
                            type(instance),
                            instance.id,
                            instance
                        )
                        logger.info(msg)
            else:
                logger.info('skip %s mapper' % mapper)
            # that's all folks :)
        return instances, error

    def set_field(self, populator, instance, mapper, field_name):
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


    def __init__(self, content, config, managed=False):
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

    def get_or_create_instance(self, mapper):
        # get or create without saving
        try:
            instance = self.Model.objects.get(
                **mapper._instance_filters
            )
            logger.info('fetched instance')
        except self.Model.DoesNotExist:
            instance = self.Model(**mapper._instance_filters)
            logger.info('created instance')
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

    def __call__(self, func):
        this = self
        @wraps(func)
        def wrapper(self):
            instances = []
            builders_args = getattr(self._mapper, func.__name__)
            for args in builders_args:
                args = list(args)
                # append current config
                args.append(self._config)
                # append managed = True
                args.append(True)
                if instance:
                    # the caller wants the instance as argument
                    args.append(self._instance)
                builder = this.BuilderClass(*args)
                p, error = builder.process_and_save()
                if error:
                    msg = '%s raised an exception' % builder
                    raise Exception(msg)
                instances.extend(p)
            return func(self, instances)
        return wrapper
