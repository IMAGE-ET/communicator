# python imports
import sys
from getopt import getopt, GetoptError

def setup_paths():
    from imagis.utils.misc import get_module_path

    workking_directory = get_module_path(__file__)
    sys.path.append(workking_directory)

def usage():
    print 'Usage: start.py -a <application main file>'
    print 'Ej: start.py -a imagis_cron'

def process_opt(args):
    try:
        opts, _ = getopt(args, 'a:h')
    except GetoptError as e:
        print e, '\n'
        usage()
        sys.exit(1)

    app = None
    for o, v in opts:
        if o == '-a':
            app = v
        elif o == '-h':
            usage()
            sys.exit(1)

    if not app:
        usage()
        sys.exit(1)
    return app

def main():
    # get the application to execute
    app = process_opt(sys.argv[1:])
    module_name = 'apps.' + app
    __import__(module_name, globals(), locals(), [], -1)
    main_func = getattr(sys.modules[module_name], 'main')
    main_func()

if __name__ == '__main__':
    main()
