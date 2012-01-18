import os
import shutil
import logging

from django.conf import settings

from util import move_file, log_exception, logger
from settings import SWALLOW_DIRECTORY


class DefaultConfig(object):
    """Main class to define a new import.

    This class is meant to be inherited and *not* used as is. You should at
    least override :method:`swallow.config.DefaultConfig.load_builder`.
    """

    @classmethod
    def input_dir(cls):
        """Directory where to looks for new files to process"""
        class_name = cls.__name__
        path = os.path.join(
            SWALLOW_DIRECTORY,
            class_name,
            'input'
        )
        return path

    @classmethod
    def work_dir(cls):
        """Directory where to store files when they are processed"""
        class_name = cls.__name__
        path = os.path.join(
            SWALLOW_DIRECTORY,
            class_name,
            'work'
        )
        return path

    @classmethod
    def done_dir(cls):
        """Directory where to store files after they are processed"""
        class_name = cls.__name__
        path = os.path.join(
            SWALLOW_DIRECTORY,
            class_name,
            'done'
        )
        return path

    @classmethod
    def error_dir(cls):
        """Directory where to store files when their import failed"""
        class_name = cls.__name__
        path = os.path.join(
            SWALLOW_DIRECTORY,
            class_name,
            'error'
        )
        return path

    def load_builder(self, *args):
        """Should load a :class`:swallow.builder.BaseBuilder` class and return
        it for processing

        If you did not override
        :method:`swallow.builder.BaseBuilder.process_and_save`
        the arguments are ``path`` of the file and a python
        ``file`` object ``f``.

        If the method returns ``None`` no processing will be done.
        """
        raise NotImplementedError()

    def __init__(self, dryrun=False):
        self.dryrun = dryrun

    def run(self):
        """Process recursivly using the BFS algorithm"""
        logger.info('run %s in %s' % (
            type(self).__name__,
            self.input_dir,
        ))
        self.process_recursively('.')

    def paths(self, path):
        """Builds paths for relative path ``path``"""
        input = os.path.realpath(os.path.join(self.input_dir(), path))
        work = os.path.realpath(os.path.join(self.work_dir(), path))
        error = os.path.realpath(os.path.join(self.error_dir(), path))
        done = os.path.realpath(os.path.join(self.done_dir(), path))
        return input, work, error, done

    def process_recursively(self, path):
        """Recusively inspect :attribute:`DefaultConfig.input_dir`
        and process files

        Recursivly inspect :attribute:`DefaultConfig.input_dir`, loads
        builder class through :method:`DefaultConfig.load_builder` and
        run processing"""
        logger.info('process_recursively %s' % path)

        input, work, error, done = self.paths(path)

        if not os.path.exists(work):
            os.makedirs(work)
        if not os.path.exists(error):
            os.makedirs(error)
        if not os.path.exists(done):
            os.makedirs(done)

        logger.info('work_path %s' % work)

        for f in os.listdir(input):
            partial_file_path = os.path.join(path, f)
            input_file_path = os.path.join(input, partial_file_path)

            if os.path.isdir(input_file_path):
                self.process_recursively(partial_file_path)
            else:
                fd = open(input_file_path)
                builder = self.load_builder(input_file_path, fd)
                if builder is None:
                    logger.info('skip file %s' % input_file_path)
                    continue
                else:
                    logger.info('match %s' % partial_file_path)
                    if not self.dryrun:
                        try:
                            builder.process_and_save()
                        except Exception, exception:
                            msg = 'wrappers generations for'
                            msg += ' %s failed' % input_file_path
                            log_exception(
                                exception,
                                msg
                            )
                            fd.close()
                            move_file(
                                input_file_path,
                                error,
                            )
                        else:
                            msg = 'success'
                            logger.info(msg)
                            fd.close()
                            move_file(
                                input_file_path,
                                done
                            )
