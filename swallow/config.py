import os
import shutil
import logging
import traceback

from django.conf import settings
from django.db.models.fields import AutoField

from facades import XmlFacade


logger = logging.getLogger()


def log_exception(
        exception,
        action,
    ):
    """log exception and move file if provided"""
    tb = traceback.format_exc()
    msg = '%s failed with %s\n%s' % (
        action,
        exception,
        tb
    )
    logger.error('%s\n%s' % (msg, tb))


def move_file(src, dst):
    logger.info('move %s to %s',
        src,
        dst,
    )
    shutil.move(src, dst)


class DefaultConfig(object):

    Facade = XmlFacade

    def __init__(self, dryrun=False):
        self.dryrun = dryrun

    @property
    def input_dir(self):
        """Directory where to looks for new files to process"""
        class_name = type(self).__name__
        path = os.path.join(
            settings.SWALLOW_DIRECTORY,
            class_name,
            'input'
        )
        return path

    @property
    def work_dir(self):
        """Directory where to store files when they are processed"""
        class_name = type(self).__name__
        path = os.path.join(
            settings.SWALLOW_DIRECTORY,
            class_name,
            'work'
        )
        return path

    @property
    def done_dir(self):
        """Directory where to store files after they are processed"""
        class_name = type(self).__name__
        path = os.path.join(
            settings.SWALLOW_DIRECTORY,
            class_name,
            'done'
        )
        return path

    def instance_is_modified(self, instance):
        raise NotImplementedError()

    @property
    def error_dir(self):
        class_name = type(self).__name__
        path = os.path.join(
            settings.SWALLOW_DIRECTORY,
            class_name,
            'error'
        )
        return path

    @property
    def Populator(self):
        return NotImplementedError()

    def match(self, file_path):
        """Filter files, if it returns True, the file is processed"""
        raise NotImplementedError()

    @property
    def model(self):
        raise NotImplementedError()

    def run(self):
        """Process recursivly using the BFS algorithm"""
        logger.info('run %s in %s' % (
            type(self).__name__,
            self.input_dir,
        ))
        self.process_recursively('.')

    def paths(self, path):
        input = os.path.realpath(os.path.join(self.input_dir, path))
        work = os.path.realpath(os.path.join(self.work_dir, path))
        error = os.path.realpath(os.path.join(self.error_dir, path))
        done = os.path.realpath(os.path.join(self.done_dir, path))
        return input, work, error, done

    def process_recursively(self, path):
        logger.info('process_recursively %s' % path)

        input, work, error, done = self.paths(path)

        if not os.path.exists(work):
            os.makedirs(work)
        if not os.path.exists(error):
            os.makedirs(error)
        if not os.path.exists(done):
            os.makedirs(done)

        logger.info('work_path %s' % work)

        for file in os.listdir(input):
            partial_file_path = os.path.join(path, file)
            input_file_path = os.path.join(input, partial_file_path)

            if os.path.isdir(input_file_path):
                self.process_recursively(partial_file_path)
            else:
                if self.match(input_file_path):
                    logger.info('match %s' % partial_file_path)
                    if not self.dryrun:
                        self.process_file(path, file)
                else:
                    logger.info('failed match for %s' % partial_file_path)

    def process_file(self, path, name):
        file_path = os.path.join(path, name)
        input, work, error, done = self.paths(file_path)

        # move the file to work dir
        move_file(input, work)

        f = open(work)

        try:
            items = self.Facade.items(file_path, f)
        except Exception, exception:
            log_exception(
                exception,
                'items generations for %s failed' % file_path
            )
            f.close()
            move_file(
                work,
                error,
            )
        else:
            try:
                for item in items:
                    self.process_item(item)
            except Exception, exception:
                log_exception(
                    exception,
                    'items processing failed'
                )
                f.close()
                move_file(
                    work,
                    error,
                )
            else:
                f.close()
                move_file(
                    work,
                    done,
                )
                logger.info('processing succeeded')

    def process_item(self, facade):
        # get or create without saving
        try:
            instance = self.model.objects.get(
                **facade.instance_filters
            )
        except self.model.DoesNotExist:
            instance = self.model(**facade.instance_filters)
        try:
            self.process_and_save(facade, instance)
        except Exception, exception:
            msg = 'processing %s' % facade
            log_exception(
                exception,
                msg,
            )
        else:
            logger.info('processing %s succeeded' % facade)

    def process_and_save(self, facade, instance):
        modified = self.instance_is_modified(instance)
        populator = self.Populator(facade, instance, modified)

        for field in instance._meta.fields:
            if isinstance(field, AutoField):
                # can't set auto field
                pass
            else:
                if populator._to_set(field.name):
                    if field.name in populator._fields_one_to_one:
                        # it's a facade property
                        value = getattr(facade, field.name)
                        setattr(instance, field.name, value)
                    else:
                        # it may be a populator method
                        method = getattr(populator, field.name, None)
                        if method is not None:
                            method()
                        # else this field doesn't need to be populated

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
