import os
import logging
import shutil
import traceback

from django.conf import settings
from django.utils.importlib import import_module


log = logging.getLogger('swallow.util')


def format_exception(exception, context_message):
    """Centralize the formatting of an exception, with traceback."""
    tb = traceback.format_exc()
    output = '\n'
    output += '*' * 80
    output += '\n'
    try:
        output += u'\n%s' % context_message
        output += u'\n%s' % exception.__class__.__name__
        output += u'\n%s' % exception.message
    except Exception, e:
        output = "\nProblem during exception message formatting, doh!"
    output = u'%s\n\n%s' % (output, tb)
    output += '\n'
    output += '_' * 80
    return output


def is_utf8(s):
    try:
        s = s.decode('utf-8')
        return True
    except:
        return False


def smart_decode(s):
    """Convert a str to unicode when you cannot be sure of its encoding."""
    if isinstance(s, unicode):
        return s
    try:
        return s.decode('utf-8')
    except:
        return s.decode('latin-1')


def move_file(src, dst):
    log.info(u'move %s to %s', smart_decode(src), smart_decode(dst))
    try:
        shutil.move(src, dst)
    except shutil.Error, exception:
        # most likely the file already exists
        log.debug(u"can't move %s to %s" % (smart_decode(src), smart_decode(dst)))
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
            log_msg = format_exception(exception, msg)
            log.error(log_msg)


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
    return CONFIGURATIONS
