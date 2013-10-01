# python imports
import sys
from getopt import getopt, GetoptError


def setup_paths():
    from imagis.utils.misc import get_module_path

    workking_directory = get_module_path(__file__)
    sys.path.append(workking_directory)

def usage():
    print 'Usage: service_manager.py -s <service> <install | remove | start | stop>'
    print 'Ej: service_manager.py -s apps.imagis_cron.imagis_cron.CronApplicationDaemon'

def process_opt(args):
    try:
        opts, _ = getopt(args, 's:h')
    except GetoptError as e:
        print e, '\n'
        usage()
        sys.exit(1)

    service = None
    for o, v in opts:
        if o == '-s':
            service = v
        elif o == '-h':
            usage()
            sys.exit(1)

    if not service:
        usage()
        sys.exit(1)
    return service

def main():
    if sys.platform == 'win32':
        try:
            import win32serviceutil
        except ImportError:
            print 'win32 extensions are not installed'
            sys.exit(1)

        setup_paths()
        service = process_opt(sys.argv[1:]).split('.')
        module, service = '.'.join(service[:-1]), service[-1]
        __import__(module, globals(), locals(), [], -1)
        service = getattr(sys.modules[module], service)

        del sys.argv[1]
        del sys.argv[1]
        win32serviceutil.HandleCommandLine(service)
    else:
        print 'for now, only win32 services are supported'

if __name__ == '__main__':
    main()
