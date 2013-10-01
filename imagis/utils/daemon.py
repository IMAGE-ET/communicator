import sys

if sys.platform == 'win32':
    try:
        import win32serviceutil
        import win32service
        import win32event
        import servicemanager
    except ImportError:
        print 'win32 extensions are not installed'
        sys.exit(1)


    class WinService(win32serviceutil.ServiceFramework):
        _svc_name_ = "WinService"
        _svc_display_name_ = "WinService"
        _svc_description_ = "WinService framework"

        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.stop_event = win32event.CreateEvent(None, 0, 0, None)

        def SvcStop(self):
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            self.stop()
            win32event.SetEvent(self.stop_event)

        def SvcDoRun(self):
            try:
                self.start()
                self.ReportServiceStatus(win32service.SERVICE_RUNNING)
                # Write an event log record
                servicemanager.LogMsg(
                    servicemanager.EVENTLOG_INFORMATION_TYPE,
                    servicemanager.PYS_SERVICE_STARTED,
                    (self._svc_name_, '')
                )

                win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)


                # Write another event log record.
                servicemanager.LogMsg(
                    servicemanager.EVENTLOG_INFORMATION_TYPE,
                    servicemanager.PYS_SERVICE_STOPPED,
                    (self._svc_name_, '')
                )
            except:
                servicemanager.LogMsg(
                    servicemanager.EVENTLOG_INFORMATION_TYPE,
                    servicemanager.PYS_SERVICE_STOPPED,
                    (self._svc_name_, ': Unexpected error')
                )

        def start(self):
            pass

        def stop(self):
            pass
    Daemon = WinService

else:
    class PosixDaemon(object):
        pass
    Daemon = PosixDaemon

def handle_service(service_cls):
    if sys.platform == 'win32':
        win32serviceutil.HandleCommandLine(service_cls)
    else:
        raise NotImplementedError, 'for now this module is only implemented for win32'
