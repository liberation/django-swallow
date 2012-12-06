import os
import shutil
from time import time
from optparse import make_option

from django.utils.importlib import import_module
from django.core.management.base import BaseCommand

from swallow.util import get_config


class Command(BaseCommand):
    args = 'import_config_module import_config_module ...'
    help = ('Executes specified clean operation for provided configuration '
            'and directories')
    option_list = BaseCommand.option_list + (
        make_option('--dryrun',
            action='store_true',
            dest='dryrun',
            default=False,
            help="Pretend to clean but don't do it"),
        make_option('--dirs',
            action='store',
            dest='dirs',
            help='Comma separated list of directories to clean (eg. "done,work")'),
        make_option('--age',
            action='store',
            dest='age',
            help='Minimum age (in seconds) a file should have to be deleted'),
        make_option('--move-to-error',
            action='store_true',
            dest='movetoerror',
            default=False,
            help='Move the selected files to error instead of deleting them'),
        )

    def handle(self, *config_module_names, **options):
        # check that command is properly parametrized
        if not config_module_names:
            print 'no configurations provided'
            return
        if options['dirs'] is None:
            print '--dirs is missing'
            return
        if options['age'] is None:
            print '--age is missing'
            return

        dryrun = options['dryrun']
        verbosity = options['verbosity']
        max_age = int(options['age'])
        dirs = options['dirs'].split(',')
        movetoerror = options['movetoerror']

        if dryrun:
            msg = 'This is a dry run. '
            msg += 'Check that your logging config is correctly set '
            msg += 'to see what happens'
            self.stdout.write(msg)

        for config_module_name in config_module_names:
            # import config class
            ConfigClass = get_config(config_module_name)

            for dir_ in dirs:
                # fetch swallow_dir
                swallow_dir = '%s_dir' % dir_
                swallow_dir = getattr(ConfigClass, swallow_dir)()

                # clean dir
                for dirpath, _, filenames in os.walk(swallow_dir):
                    for filename in filenames:
                        file_path = os.path.join(dirpath, filename)
                        st_mtime = os.stat(file_path).st_mtime
                        age = time() - st_mtime

                        if age > max_age:
                            if verbosity > 0:  # Use --verbosity=0 to make it quiet
                                self.stdout.write("%s is to be deleted\n" % file_path)
                            if not dryrun:
                                if movetoerror:
                                    duplicate_path = getattr(ConfigClass, 'duplicate_dir')()
                                    try:
                                        os.mkdir(duplicate_path)
                                    except OSError,e:
                                        pass # the directory already exists
                                    new_file_path = os.path.join(duplicate_path, filename)
                                    shutil.move(file_path, new_file_path)
                                else:
                                    os.remove(file_path)
