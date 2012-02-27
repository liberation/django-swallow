import os
from time import time
from optparse import make_option

from django.utils.importlib import import_module
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    args = 'import_config_module swallow_dir_name max_age'
    help = '''Executes specified clean operation on ``swallow_dir``
            of configuration ``import_config_module``'''

    option_list = BaseCommand.option_list + (
        make_option('--dryrun',
            action='store_true',
            dest='dryrun',
            default=False,
            help="Pretend to do the import but don't do it"),
        )

    def handle(self, *args, **options):
        dryrun = options['dryrun']

        if dryrun:
            msg = 'This is a dry run. '
            msg += 'Check that your logging config is correctly set '
            msg += 'to see what happens'
            self.stdout.write(msg)

        # assign options
        import_config_module = args[0]
        swallow_dir = args[1]
        max_age = int(args[2])

        # import config class
        import_config_module = import_config_module.split('.')
        class_name = import_config_module[-1]
        import_config_module = '.'.join(import_config_module[:-1])
        config_module = import_module(import_config_module)
        ConfigClass = getattr(config_module, class_name)

        # fetch swallow_dir 
        swallow_dir = getattr(ConfigClass, swallow_dir)()

        # clean dir
        for dirpath, _, filenames in os.walk(swallow_dir):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                st_mtime = os.stat(file_path).st_mtime
                age = time() - st_mtime
                if age > max_age:
                    self.stdout.write('%s is to be deleted' % file_path)
                    if not dryrun:
                        os.remove(file_path)
