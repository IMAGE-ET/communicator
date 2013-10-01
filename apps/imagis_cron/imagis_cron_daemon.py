# python imports
import sys

# iMagis imports
from apps.imagis_cron.imagis_cron import CronApplication
from imagis.utils.daemon import handle_service, Daemon

class CronApplicationDaemon(Daemon):

    _svc_name_ = "imagis_cron"
    _svc_display_name_ = "iMagis Cron"
    _svc_description_ = "Service to schedule periodic task"

    def start(self):
        self.app = CronApplication()
        self.app.start()

    def stop(self):
        self.app.stop()

def main():
    if __name__ != '__main__':
        print 'this module cannot be imported, use it as standalone module'
        sys.exit(1)
    handle_service(CronApplicationDaemon)

if __name__ == '__main__':
    main()

