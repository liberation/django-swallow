from optparse import make_option

from django.utils.importlib import import_module
from django.core.management.base import BaseCommand

from swallow.util import get_config

class Command(BaseCommand):
    args = '<import_config_module import_config_module ...>'
    help = 'Executes specified imports'

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

        for import_config_module in args:
            ConfigClass = get_config(import_config_module)
            config = ConfigClass(dryrun)
            config.run()
