# -*- coding: UTF-8 -*-

# python imports
import os
import sys

# twisted imports
from twisted.web import server, resource, static
from twisted.internet import reactor

# imagis imports
from imagis.utils.logs import setup_logger
from imagis.utils.misc import set_exit_handler
from imagis.utils.daemon import Daemon
try:
    import config.store_server as config
except ImportError:
    class config:
        app = {}
        logger = {}
        server = {}

# store server imports
from store_service import StoreService
from cmove_webservice import MoveFilesXMLRPC
from cfind_webservice import WCFind
# setup logger
logger = setup_logger(
    'store_server',
    log_file=config.logger.get('log_file', 'store_server.log'),
    max_bytes=config.logger.get('max_bytes', 1048576),
    count=config.logger.get('count', 3)
)

class DicomWebServicesApp(object):

    def __init__(self):
        set_exit_handler(self._exit_handler)

        usr = "store_user"
        passwd = "store_passwd"
        
        home_path = config.server.get('home_path', os.environ['HOME'])
                
        iMagisCommunicator_path = os.path.join(home_path, 'iMagisCommunicator')
        upload_path = os.path.join(iMagisCommunicator_path, 'uploaded')
        failed_files = os.path.join(upload_path, 'failed_files')
        logs_path = os.path.join(iMagisCommunicator_path, 'logs')
        www_path = os.path.join(iMagisCommunicator_path, 'download')
        move_path = os.path.join(iMagisCommunicator_path, 'dcm_move')
        if os.path.isdir(iMagisCommunicator_path) == False:
            os.mkdir(iMagisCommunicator_path)
            os.mkdir(upload_path)
            os.mkdir(failed_files)
            os.mkdir(logs_path)
            os.mkdir(www_path)
            os.mkdir(move_path)
      
        self.store_server = StoreService(
            upload_path,
            failed_files,
            user=usr,
            password=passwd
        )
        self.move_server = MoveFilesXMLRPC(
            logs_path, 
            config, 
            www_path,
            move_path,
            user = usr, 
            password= passwd
        )
        self.find_server = WCFind(
            logs_path, 
            config, 
            user = usr, 
            password = passwd
        )
        self.web_server = static.File(www_path)

    def start(self):
        try:
            ip = config.server.get('ip', '127.0.0.1')
            port = config.server.get('port', 8080)

            root = resource.Resource()
            root.putChild('XMLRPC', self.store_server)
            root.putChild('MOVE-XMLRPC', self.move_server)
            root.putChild('FIND-XMLRPC', self.find_server)
            root.putChild('iMagis', self.web_server)

            site = server.Site(root)
            reactor.listenTCP(port, site, interface=ip)

            logger.info('starting applications_server, listening in: %s:%s' % (ip, port))
            reactor.run()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        logger.info('stopping store_server...')
        reactor.stop()

    def _exit_handler(self, signum, frame=None):
        self.stop()

    def _create_server_dirs(self, upload_path, failed_files):
        try:
            for folder in (upload_path, failed_files):
                if not os.path.exists(folder):
                    logger.info('creating server folder: %s' % folder)
                    os.makedirs(folder)
        except OSError as e:
            print e
            sys.exit(1)

def main():
    app = DicomWebServicesApp()
    app.start()

if __name__ == '__main__':
    main()

