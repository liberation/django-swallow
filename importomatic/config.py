import os, re, shutil, logging

from django.conf import settings
from django.shortcuts import get_object_or_404


logger = logging.getLogger()


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
        raise NotImplemented()

    @property
    def model(self):
        raise NotImplemented()

    @property
    def Facade(self):
        """Facade class used to wrap the file to be processed. Its
        constructor receive the ``file_path`` of file to wrap.
        """
        raise NotImplemented()

    def process(self, facade, instance):
        raise NotImplemented()

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
                    input_file_path = os.path.realpath(input_file_path)
                    logger.info('match %s' % input_file_path)

                    # the file match configuration
                    work_file_path = os.path.join(work_path, name)
                    done_file_path = os.path.join(done_path, name)
                    error_file_path = os.path.join(error_path, name)

                    # move the file to work dir
                    if not self.dryrun:
                        shutil.move(input_file_path, work_file_path)

                        f = open(work_file_path)

                        # build facade
                        file_path = os.path.join(path, name)
                        facade = self.Facade(file_path, f)

                        # get or create instance
                        instance = self.model.objects.get_or_create(
                            **facade.instance_filters
                        )

                        logger.info('process')
                        try:
                            self.process(facade, instance)
                        except Exception, e:
                            msg = 'Processing %s raised %s: %s' % (
                                os.path.join(root, name),
                                e,
                                e.message
                            )
                            logger.error(msg)
                            logger.info('move %s to %s',
                                work_file_path,
                                error_file_path,
                            )
                            shutil.move(work_file_path, error_file_path)
                        else:
                            logger.info('move %s to %s' % (
                                work_file_path,
                                done_file_path,
                            ))
                            shutil.move(work_file_path, done_file_path)
                        f.close()
                        logger.info('close')
            # recurse!
            for subdir in dirs:
                new_path = os.path.join(path, subdir)
                self.process_recursively(new_path)
