# python imports
import os
import sys
import shutil
import logging
import threading

# imagis imports
import imagis
import apps.imagis_cron.tasks as tasks
from imagis.utils.dir import files_from
from imagis.utils.process import get_output
from apps.imagis_cron.cron import StopTask

WINDOWS = sys.platform == 'win32'
logger = logging.getLogger('imagis_cron.task_http_send')
spool_lock = threading.Lock()
analyzed_spools = set()

def _check_stop(spool, nfiles, nsent_files):
    # if instructed to stop, just do it
    if tasks.stop:
        logger.info('%s files of %s in: %s were sent' % (nsent_files, nfiles, spool))
        raise StopTask

def _lock_spool(spool):
    with spool_lock:
        if spool in analyzed_spools:
            raise StopTask
        analyzed_spools.add(spool)

def _unlock_spool(spool):
    with spool_lock:
        analyzed_spools.discard(spool)

def http_send(url, spool, buffer=8192):
    nfiles, nsent_files = 0, 0

    try:
        # check that this task is not locked
        _lock_spool(spool)
    except StopTask:
        return
    
    try:
        # if instructed to stop, just do it
        _check_stop(spool, nfiles, nsent_files)
 
        logger.info('starting to send files in: %s to: %s' % (spool, url))

        # create the log folder if there is none
        try:
            log_folder = os.path.join(spool, 'client')
            if not os.path.exists(log_folder):
                os.makedirs(log_folder)
        except OSError as e:
            logger.error(e)
            return

        # if instructed to stop, just do it
        _check_stop(spool, nfiles, nsent_files)

        path = os.path.join(imagis.THIRD_PARTY_DIR, 'http_sender', 'http_sender.py')
        to_continue = '-'.join(os.listdir(log_folder))
        for file_path in files_from(spool, True):

            # if instructed to stop, just do it
            _check_stop(spool, nfiles, nsent_files)

            # do not process the log folder
            if log_folder in file_path:
                continue

            space = ' ' if WINDOWS else '\ '
            cmd = ' '.join((
                'python',
                path ,
                '-U %s' % url,
                '-f %s' % file_path.replace(' ', space),
                '-l %s' % log_folder.replace(' ', space),
                '-u store_user',
                '-p store_passwd',
                '-b %s' % buffer,
            ))

            file_name = os.path.basename(file_path)
            incomplete = ''
            if file_name in to_continue:
                # need to be continued
                cmd = cmd + ' -R'
                incomplete = 'incomplete'

            logger.info('starting to send %s file: %s' % (incomplete, file_name))

            _, output, _ = get_output(cmd)

            # if instructed to stop, just do it
            _check_stop(spool, nfiles, nsent_files)

            error = process_output(file_path, output)

            # count the number of successfully sent files
            if not error:
                nsent_files += 1
            nfiles += 1

        logger.info('%s files of %s in: %s were sent' % (nsent_files, nfiles, spool))

    except StopTask:
        pass
    finally:
        # remove spool from the list of analyzed spools
        _unlock_spool(spool)

def process_output(file_path, output):
    for line in output.splitlines():
        if 'registered in server' in line:
            try:
                os.remove(file_path)
                logger.info('finished sending file: %s' % file_path)
                return False
            except (OSError, IOError, shutil.Error) as e:
                logger.error(e.strerror)
                return False

    logger.error('error sending file: %s' % file_path)
    return True


