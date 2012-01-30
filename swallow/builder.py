import logging
from functools import wraps

from util import log_exception, logger

from django.db.models.fields import AutoField
from django.db import IntegrityError
from django.db.transaction import commit_manually


logger = logging.getLogger()


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
        """Django Model class to instatiate and populate."""
        raise NotImplementedError()

    @property
    def Populator(self):
        """Class that populates instances see
        :class:`swallow.populator.Populator`.
        """
        raise NotImplementedError()

    def instance_is_locally_modified(self, instance):
        """Should return a boolean. Used to know whether the instance
        was modified locally or not. The swallow use this value to know
        if it should or not populate the instance
        """
        raise NotImplementedError()

    def skip(self, mapper):
        """Should return a boolean. Used to know whether to use this mapper
        to create/update an instance.
        """
        raise NotImplementedError()

    def process_and_save(self):
        """Builds :class:`swallow.mappers.Mapper` classes, instantiate models
        and populate them with the help of a populator.

        if ``managed``` is set to ``False`` the function won't try to commit
        transaction.
        """
        instances = []

        for mapper in self.Mapper._iter_mappers(self.path, self.fd):
            try:
                with commit_manually():
                    logger.info('processing of %s mapper starts' % mapper)
                    if not self.skip(mapper):
                        instance = self.__get_or_create(mapper)
                        instances.append(instance)
                        modified = self.instance_is_locally_modified(instance)
                        populator = self.Populator(mapper, instance, modified)
                        for field in instance._meta.fields:
                            if isinstance(field, AutoField):
                                # can't set auto field
                                pass
                            else:
                                if populator._to_set(field.name):
                                    self.__set_field_name(
                                        instance,
                                        populator,
                                        mapper,
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
                                    f = getattr(instance, field.name)
                                    f.clear()  # XXX: add a hook to overide
                                               # this behaviour
                                    method()
                                # else ``method`` is not set
                                # no need to set this field
                        msg = 'saved %s@%s: %s' % (
                            type(instance),
                            instance.id,
                            instance
                        )
                        logger.info(msg)
                    else:
                        logger.info('skip %s mapper' % mapper)
                    # that's all folks :)
            except IntegrityError, e:
                log_exception(e, 'database save')
        return instances

    def __init__(self, path, fd, config=None):
        self.path = path
        self.fd = fd
        self.config = config

    def __set_field_name(self, instance, populator, mapper, field_name):
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

    def __get_or_create(self, mapper):
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

    def __init__(self, BuilderClass):
        self.BuilderClass = BuilderClass

    def __call__(self, func):
        this = self
        @wraps(func)
        def wrapper(self):
            photos = []
            builders_args = getattr(self._mapper, func.__name__)
            for args in builders_args:
                builder = this.BuilderClass(*args)
                photos.extend(builder.process_and_save())
            return func(self, photos)
        return wrapper
