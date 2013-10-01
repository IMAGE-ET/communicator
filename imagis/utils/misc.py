# python imports
import platform, os

def get_system_name():
    """
    Return the system identification name. Posible 
    values until now are: (linux, windows, mac).
    
    get_system_name(): str 
    """
    system_name = platform.system().lower()
    if system_name in ['linux']:
        return 'linux'
    elif system_name in ['windows', 'microsoft']:
        return 'windows'
    elif system_name in ['darwin', 'mac', 'macosx']:
        return 'mac'
    else:
        raise 'iMagis could not detect your system: %s' % system_name

def get_module_path(module_file_path):
    """
    Get the module directory path 
    
    get_module_path(module_file_path: str): str
    """
    import os
    module_path = os.path.split(module_file_path)[0]
    if module_path:
        # this module was not is in the current directory
        return module_path

    # this module was is in the current directory
    return os.getcwd()

def whereis(program):
    for path in os.environ.get('PATH', '').split(':'):
        if os.path.exists(os.path.join(path, program)) and \
           not os.path.isdir(os.path.join(path, program)):
            return os.path.join(path, program)
    return None

def set_exit_handler(handler_func):
    import sys

    if sys.platform == "win32":
        try:
            import win32api
            win32api.SetConsoleCtrlHandler(handler_func, True)
        except ImportError:
            version = ".".join(map(str, sys.version_info[:2]))
            raise Exception("pywin32 not installed for Python " + version)
    else:
        import signal
        signals = (
            signal.SIGTERM,
            signal.SIGILL,
            signal.SIGABRT,
            signal.SIGINT,
            signal.SIGPWR,
            signal.SIGQUIT,
            signal.SIGHUP,
            signal.SIGALRM
        )
        for sig in signals:
            signal.signal(sig, handler_func)

