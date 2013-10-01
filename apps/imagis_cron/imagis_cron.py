# python imports
import os

# iMagis imports
from cron import Cron
from imagis.utils.logs import setup_logger
from imagis.utils.misc import set_exit_handler
from imagis.utils.daemon import Daemon
try:
    import config.imagis_cron as config
except ImportError:
    class config:
        app = {}
        logger = {}
        tasks = {}

# setup logger
logger = setup_logger(
    'imagis_cron',
    log_file = config.logger.get('log_file', 'imagis_cron.log'),
    max_bytes = config.logger.get('max_bytes', 1048576),
    count=config.logger.get('count', 3)
)

class CronApplication(object):

    def __init__(self):
        self.cron = Cron(config.tasks)
        set_exit_handler(self._exit_handler)

    def start(self):
        try:
            self.cron.start()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.cron.stop()

    def _exit_handler(self, signum, frame=None):
        self.cron.stop()

def main():
    app = CronApplication()
    app.start()

