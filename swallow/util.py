import logging
import shutil
import traceback


logger = logging.getLogger()


def log_exception(
        exception,
        action,
    ):
    """log exception and move file if provided"""
    tb = traceback.format_exc()
    msg = '%s failed with %s\n%s' % (
        action,
        exception,
        tb
    )
    logger.error('%s\n%s' % (msg, tb))


def move_file(src, dst):
    logger.info('move %s to %s',
        src,
        dst,
    )
    shutil.move(src, dst)
