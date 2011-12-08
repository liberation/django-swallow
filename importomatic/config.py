import os, re, shutil, logging, traceback

from lxml import etree

from django.conf import settings
from django.db.models.fields.related import ManyToManyField

from models import Matching
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

    def __init__(self, dryrun=False):
        self.dryrun = dryrun

    @property
    def input_dir(self):
        """Directory where to looks for new files to process"""
        class_name = type(self).__name__
        path = os.path.join(settings.IMPORTOMATIC_DIR, class_name, 'input')
        return path

    @property
    def work_dir(self):
        """Directory where to store files when they are processed"""
        class_name = type(self).__name__
        path = os.path.join(settings.IMPORTOMATIC_DIR, class_name, 'work')
        return path

    @property
    def done_dir(self):
        """Directory where to store files after they are processed"""
        class_name = type(self).__name__
        path = os.path.join(settings.IMPORTOMATIC_DIR, class_name, 'done')
        return path

    @property
    def error_dir(self):
        class_name = type(self).__name__
        path = os.path.join(settings.IMPORTOMATIC_DIR, class_name, 'error')
        return path

    def match(self, file_path):
        """Filter files, if it returns True, the file is processed"""
        raise NotImplementedError()

    @property
    def model(self):
        raise NotImplementedError()

    def items(self, file_path, content):
        element = etree.fromstring(content)
        return [element]

    Facade = XmlFacade

    def process(self, facade, instance):
        raise NotImplementedError()

    def run(self):
        """Process recursivly using the BFS algorithm"""
        logger.info('run %s in %s' % (
            type(self).__name__,
            self.input_dir,
        ))
        self.process_recursively('.')

    def process_recursively(self, path):
        logger.info('process_recursively %s' % path)

        work_path = os.path.realpath(os.path.join(self.work_dir, path))
        if not os.path.exists(work_path):
            os.makedirs(work_path)

        error_path = os.path.realpath(os.path.join(self.error_dir, path))
        if not os.path.exists(error_path):
            os.makedirs(error_path)

        done_path = os.path.realpath(os.path.join(self.done_dir, path))
        if not os.path.exists(done_path):
            os.makedirs(done_path)

        logger.info( 'work_path %s' % work_path)
        input_path = os.path.realpath(os.path.join(self.input_dir, path))
        logger.info('walk %s' % input_path)
        for root, dirs, files in os.walk(input_path):
            # process all files in this level
            for name in files:
                input_file_path = os.path.join(input_path, name)
                if self.match(input_file_path):
                    # the file match configuration
                    logger.info('match %s' % input_file_path)

                    work_file_path = os.path.join(work_path, name)
                    done_file_path = os.path.join(done_path, name)
                    error_file_path = os.path.join(error_path, name)

                    # move the file to work dir
                    if not self.dryrun:
                        move_file(input_file_path, work_file_path)
                        f = open(work_file_path)
                        content = f.read()
                        f.close()
                        # build facade
                        file_path = os.path.join(path, name)

                        try:
                            items = self.items(file_path, content)
                        except Exception, exception:
                            log_exception(
                                exception,
                                '%s items generations failed' % file_path
                            )
                            move_file(
                                work_file_path,
                                error_file_path,
                            )
                            continue  # next file

                        for item in items:
                            try:
                                facade = self.Facade(file_path, content, item)
                            except Exception, exception:
                                msg = '%s Facade creation for %s' % (
                                    file_path,
                                    item
                                )
                                log_exception(
                                    exception,
                                    msg,
                                )
                                continue  # next item

                            # get or create instance
                            instance, created = self.model.objects.get_or_create(
                                **facade.instance_filters
                            )

                            logger.info('process')
                            try:
                                self.process(facade, instance)
                            except Exception, exception:
                                msg = '%s processing %s' % (
                                    file_path,
                                    item
                                )
                                log_exception(
                                    exception,
                                    msg,
                                )
                                continue  # next item
                            else:
                                move_file(work_file_path, done_file_path)
            # recurse!
            for subdir in dirs:
                new_path = os.path.join(path, subdir)
                self.process_recursively(new_path)

    def populate_from_matching(
            self,
            matching_name,
            facade,
            instance,
            field_name,
            first_matching=False,
            get_or_create_related=None,
            create_through=None,
        ):

        # exceptions are catched in ``process_recursively``
        matching = Matching.objects.get(name=matching_name)

        # fetch field for ``field_name``

        if field_name in instance._meta.get_all_field_names():
            field = instance._meta.get_field_by_name(field_name)[0]
        else:
            msg = 'field %s not found on %s.' % (field_name, instance)
            raise Exception(msg)

        if isinstance(field, ManyToManyField):
            # it's a M2M field
            values = matching.match(facade, first_matching)
            for value in values:
                if get_or_create_related is None:
                    msg = 'Try to set a related  property without '
                    msg += '``get_or_create_related`` provided.'
                    raise Exception(msg)
                else:
                    related, created = get_or_create_related(
                        facade,
                        instance,
                        value,
                    )
                    if created:
                        related.save()
                    if create_through is None:
                        # let's try to add the generic M2M
                        field = getattr(instance, field_name)
                        field.add(related)
                    else:
                        through = create_through(
                            related,
                            instance,
                            facade,
                        )
                        through.save()
        else:
            # since it's a property we only need one value
            # force first_match
            values = matching.match(facade, first_matching=True)
            setattr(instance, field_name, values[0])
