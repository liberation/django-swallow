import os
import logging
import shutil
import traceback

from django.conf import settings
from django.utils.importlib import import_module


logger = logging.getLogger()


def log_exception(
        exception,
        action,
    ):
    """log exception and move file if provided"""
    tb = traceback.format_exc()
    msg = '%s with %s' % (
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


def get_config(path):
    """
    Return a config class from its module path.
    """
    import_config_module = path.split('.')
    class_name = import_config_module[-1]
    import_config_module = '.'.join(import_config_module[:-1])
    config_module = import_module(import_config_module)
    return getattr(config_module, class_name)

# list configurations classes
def get_configurations():
    CONFIGURATIONS = {}
    for path in getattr(settings, "SWALLOW_CONFIGURATION_MODULES", []):
        config_class = get_config(path)
        CONFIGURATIONS[config_class.__name__] = config_class
    print CONFIGURATIONS
    return CONFIGURATIONS
