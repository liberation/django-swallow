import os
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
            os.remove(src)
        else:  # arg! it's something else
               # keep the file we don't want to loose data
            log_exception(exception, 'move %s to %s' % (src, dst))
