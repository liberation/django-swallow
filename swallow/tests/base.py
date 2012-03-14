import os
import shutil

from django.test import TransactionTestCase


CURRENT_PATH = os.path.dirname(__file__)


class BaseSwallowTests(TransactionTestCase):

    def setUp(self):
        self.SWALLOW_DIRECTORY = os.path.join(CURRENT_PATH, 'import')

        self.import_dir = os.path.join(CURRENT_PATH, 'import')
        if os.path.exists(self.import_dir):
            shutil.rmtree(self.import_dir)
        import_initial = os.path.join(CURRENT_PATH, 'import.initial')
        shutil.copytree(import_initial, self.import_dir)

    def tearDown(self):
        shutil.rmtree(self.import_dir)
