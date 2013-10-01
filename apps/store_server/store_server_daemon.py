# -*- coding: UTF-8 -*-

# python imports
import sys

# iMagis imports
from apps.store_server.store_server import StoreServerApplication
from imagis.utils.daemon import handle_service, Daemon

class StoreServerApplicationDaemon(Daemon):

    _svc_name_ = "imagis_store_server"
    _svc_display_name_ = "iMagis Store Server"
    _svc_description_ = "Service to receive files by http"

    def start(self):
        self.app = StoreServerApplication()
        self.app.start()

    def stop(self):
        self.app.stop()

def main():
    if __name__ != '__main__':
        print 'this module cannot be imported, use it as standalone module'
        sys.exit(1)
    handle_service(StoreServerApplicationDaemon)

if __name__ == '__main__':
    main()

