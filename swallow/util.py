import os
import logging
import shutil
import traceback

from django.conf import settings
from django.utils.importlib import import_module

from settings import SWALLOW_CONFIGURATION_MODULES

logger = logging.getLogger()


def log_exception(
        exception,
        action,
    ):
    """log exception and move file if provided"""
    tb = traceback.format_exc()
    msg = '%s failed with %s' % (
        action,
        exception
    )
    logger.error('%s\n%s' % (msg, tb))


def move_file(src, dst):
    logger.info('move %s to %s',
        src,
        dst,
    )
    try:
        shutil.move(src, dst)
    except shutil.Error, exception:
        # most likely the file already exists
        logger.debug("can't move %s to %s" % (src, dst))
        dst_file = os.path.join(dst, os.path.basename(src))
        if os.path.exists(dst_file):
            # if the file already exists the import failed previously
            # no need to move this file again since afp xml files
            # are properly versionned we are assured that it's the
            # same file
            os.remove(src)
        else:  # arg! it's something else
               # keep the file we don't want to loose data
            msg = '%s is buggy, tried to move to error but failed' % src
            log_exception(exception, msg)


# list configurations classes
CONFIGURATIONS = {}
for configuration_module in SWALLOW_CONFIGURATION_MODULES:
    from config import DefaultConfig  # avoids circular imports
    modules = import_module(configuration_module)
    for cls in vars(modules).values():

        if (isinstance(cls, type)
            and issubclass(cls, DefaultConfig)
            and cls is not DefaultConfig):
            CONFIGURATIONS[cls.__name__] = cls
