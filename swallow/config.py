import os
import logging

from time import time

from django.conf import settings

from swallow.exception import StopConfig


logger = logging.getLogger('swallow.config')


class BaseConfig(object):
    """Main class to define a new import.

    This class is meant to be inherited and *not* used as is. You should at
    least override :method:`swallow.config.BaseConfig.load_builder`.
    """

    @classmethod
    def input_dir(cls):
        """Directory where to looks for new files to process"""
        class_name = cls.__name__.lower()
        path = os.path.join(
            settings.SWALLOW_DIRECTORY,
            class_name,
            'input'
        )
        return path

    @classmethod
    def work_dir(cls):
        """Directory where to store files when they are processed"""
        class_name = cls.__name__.lower()
        path = os.path.join(
            settings.SWALLOW_DIRECTORY,
            class_name,
            'work'
        )
        return path

    @classmethod
    def done_dir(cls):
        """Directory where to store files after they are processed"""
        class_name = cls.__name__.lower()
        path = os.path.join(
            settings.SWALLOW_DIRECTORY,
            class_name,
            'done'
        )
        return path

    @classmethod
    def error_dir(cls):
        """Directory where to store files when their import failed"""
        class_name = cls.__name__.lower()
        path = os.path.join(
            settings.SWALLOW_DIRECTORY,
            class_name,
            'error'
        )
        return path

    def load_builder(self, partial_file_path):
        """Should load a :class`:swallow.builder.BaseBuilder` class and return
        it for processing.

        If you did not override
        :method:`swallow.config.BaseConfig.run` or
        :method:`swallow.config.BaseConfig.process_recursively`
        the arguments are ``partial_file_path``.

        If the method returns ``None`` the file will be skipped.
        """
        raise NotImplementedError()

    def __init__(self, dryrun=False):
        self.dryrun = dryrun

        self.files = []  # this is the current list of files processed
                         # by swallow
                         # FIXME: explain how it works

        self.on_error = False  # this should reset at for each file

    def open(self, relative_path):
        from util import move_file
        path = os.path.join(
            self.input_dir(),
            relative_path
        )
        work = os.path.join(self.work_dir(), relative_path)
        move_file(
            path,
            work
        )
        self.files.append(relative_path)
        f = open(work)
        return f

    def run(self):
        """Process recursivly ``input_dir``"""
        logger.info('run %s in %s' % (
            type(self).__name__,
            self.input_dir(),
        ))
        self.process_recursively()

    def paths(self, path):
        """Builds paths for relative path ``path``"""
        input = os.path.realpath(os.path.join(self.input_dir(), path))
        work = os.path.realpath(os.path.join(self.work_dir(), path))
        error = os.path.realpath(os.path.join(self.error_dir(), path))
        done = os.path.realpath(os.path.join(self.done_dir(), path))
        return input, work, error, done

    def mv_files_from_work_dir(self, to_dir):
        """Move current endpoints files from work dir to to_dir."""
        from util import move_file  # FIXME
        # Move the endpoint files
        for p in self.files:
            work = os.path.join(self.work_dir(), p)
            target = os.path.join(to_dir, p)
            move_file(
                work,
                target
            )
        self.files = []

    def process_recursively(self, path=""):
        """Recusively inspect :attribute:`BaseConfig.input_dir`
        and process files using BFS

        Recursivly inspect :attribute:`BaseConfig.input_dir`, loads
        builder class through :method:`BaseConfig.load_builder` and
        run processing"""

        instances = None
        if hasattr(self, 'postprocess'):
            instances = []

        # avoids circular imports
        from util import log_exception, move_file  # FIXME

        logger.info('process_recursively %s' % path)

        input, work, error, done = self.paths(path)

        if not os.path.exists(work):
            os.makedirs(work)
        if not os.path.exists(error):
            os.makedirs(error)
        if not os.path.exists(done):
            os.makedirs(done)
        # input_dir should exists

        logger.info('work_path %s' % work)

        for f in os.listdir(input):
            # Relative file path from current path
            partial_file_path = os.path.join(path, f)
            # Absolute file path
            input_file_path = os.path.join(input, f)

            if os.path.isdir(input_file_path):
                self.process_recursively(partial_file_path)
            else:
                if not os.path.exists(input_file_path):
                    # the file might have been already moved
                    # by a nested builder
                    continue

                # --- Check file age
                # Idea is to prevent from processing a file too much recent, to
                # avoid processing file while they are downloaded in input dir
                # and to minimize risk of missing dependency files
                # If you don't care about this, just do not set it in settings
                min_age = getattr(settings, "SWALLOW_QUARANTINE", 0)  # seconds
                if min_age > 0:
                    st_mtime = os.stat(input_file_path).st_mtime
                    age = time() - st_mtime
                    if age < min_age:
                        logger.info("Skipping too recent file %s" % input_file_path)
                        continue

                # --- Load and process builder for file
                builder = self.load_builder(partial_file_path)
                if builder is None:
                    logger.info('skip file %s' % input_file_path)
                    continue
                else:
                    logger.info('match %s' % partial_file_path)
                    if not self.dryrun:
                        try:
                            new_instances = builder.process_and_save()
                        except StopConfig, e:
                            # this is a user controlled exception
                            msg = u'Import stopped for %s' % self
                            msg += u"Reason is: \n%s" % e.message
                            logger.warning(msg)
                            self.mv_files_from_work_dir(to_dir=self.error_dir())
                            break
                        except Exception, exception:
                            msg = 'builder processing of'
                            msg += ' %s failed' % input_file_path
                            log_exception(
                                exception,
                                msg
                            )
                            self.mv_files_from_work_dir(to_dir=self.error_dir())
                        else:
                            if hasattr(self, 'postprocess'):
                                instances.append(new_instances)
                            self.mv_files_from_work_dir(to_dir=self.done_dir())
                    else:
                        # We are in dry-run, put back the files in input dir
                        self.mv_files_from_work_dir(to_dir=self.input_dir())

        # --- Clean old files from current input directory
        if not self.dryrun:
            # Here is the simplest implementation to manage secondary files
            # i.e. files that has not been endpoint files
            # These files could have been used has dependency file, by one or
            # more import
            # We need to manage to cases:
            # - the case of a file that is a dependency of two endpoints files
            # - the case of a file that is a dependency of a endpoint file that
            #   has gone in error
            # Both these cases should better be handled with transaction, but
            # we consider that the transaction implementation in Django is not
            # enouth advanced for these complex cases (m2m, post_save, etc.)
            # (See for example ticket #14051 in Django Trac)
            # When the Implementor has used Config.open to manage these files,
            # they already have been moved away
            for f in os.listdir(input):
                input_file_path = os.path.join(input, f)
                done_file_path = os.path.join(done, f)
                grace_period = getattr(settings, "SWALLOW_GRACE_PERIOD", 60 * 60 * 24)
                st_mtime = os.stat(input_file_path).st_mtime
                age = time() - st_mtime
                if age > grace_period:
                    logger.info("Removing old file from input dir: %s" % input_file_path)
                    move_file(input_file_path, done_file_path)

        if hasattr(self, 'postprocess'):
            self.postprocess(instances)
