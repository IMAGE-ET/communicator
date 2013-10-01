import os
import subprocess
import errno
from cStringIO import StringIO

PIPE = subprocess.PIPE
STDOUT = subprocess.STDOUT

if subprocess.mswindows:
    try:
        import win32process, win32con
        STARTUPINFO = win32process.STARTUPINFO
        SW_HIDE = win32con.SW_HIDE
        STARTF_USESHOWWINDOW = win32con.STARTF_USESHOWWINDOW
    except ImportError:
        STARTUPINFO = subprocess.STARTUPINFO
        STARTF_USESHOWWINDOW = 0
        SW_HIDE = 0

if subprocess.mswindows:
    from win32file import ReadFile, WriteFile
    from win32pipe import PeekNamedPipe
    import msvcrt
else:
    import select
    import fcntl

class Popen(subprocess.Popen):

    def readline(self):
        return self._readline('stdout')

    def readline_err(self):
        return self._readline('stderr')

    def _readline(self, channel):
        recv_func = None
        if channel == 'stdout':
            recv_func = self.recv
        elif channel == 'stderr':
            recv_func = self.recv_err

        if not recv_func:
            raise StopIteration

        while self.poll() is None:
            result = recv_func()
            if result:
                io = StringIO(result)
                line = io.readline()
                while line:
                    yield line
                    line = io.readline()

    def recv(self, maxsize=None):
        return self._recv('stdout', maxsize)

    def recv_err(self, maxsize=None):
        return self._recv('stderr', maxsize)

    def send_recv(self, input='', maxsize=None):
        return self.send(input), self.recv(maxsize), self.recv_err(maxsize)

    def get_conn_maxsize(self, which, maxsize):
        if maxsize is None:
            maxsize = 1024
        elif maxsize < 1:
            maxsize = 1
        return getattr(self, which), maxsize

    def _close(self, which):
        getattr(self, which).close()
        setattr(self, which, None)

    if subprocess.mswindows:
        def send(self, input):
            if not self.stdin:
                return None

            try:
                x = msvcrt.get_osfhandle(self.stdin.fileno())
                (errCode, written) = WriteFile(x, input)
            except ValueError:
                return self._close('stdin')
            except (subprocess.pywintypes.error, Exception), why:
                if why[0] in (109, errno.ESHUTDOWN):
                    return self._close('stdin')
                raise

            return written

        def _recv(self, which, maxsize):
            conn, maxsize = self.get_conn_maxsize(which, maxsize)
            if conn is None:
                return None

            try:
                x = msvcrt.get_osfhandle(conn.fileno())
                (read, nAvail, nMessage) = PeekNamedPipe(x, 0)
                if maxsize < nAvail:
                    nAvail = maxsize
                if nAvail > 0:
                    (errCode, read) = ReadFile(x, nAvail, None)
            except ValueError:
                return self._close(which)
            except (subprocess.pywintypes.error, Exception), why:
                if why[0] in (109, errno.ESHUTDOWN):
                    return self._close(which)
                raise

            if self.universal_newlines:
                read = self._translate_newlines(read)
            return read

    else:
        def send(self, input):
            if not self.stdin:
                return None

            if not select.select([], [self.stdin], [], 0)[1]:
                return 0

            try:
                written = os.write(self.stdin.fileno(), input)
            except OSError, why:
                if why[0] == errno.EPIPE: #broken pipe
                    return self._close('stdin')
                raise

            return written

        def _recv(self, which, maxsize):
            conn, maxsize = self.get_conn_maxsize(which, maxsize)
            if conn is None:
                return None

            flags = fcntl.fcntl(conn, fcntl.F_GETFL)
            if not conn.closed:
                fcntl.fcntl(conn, fcntl.F_SETFL, flags | os.O_NONBLOCK)

            try:
                if not select.select([conn], [], [], 0)[0]:
                    return ''

                r = conn.read(maxsize)
                if not r:
                    return self._close(which)

                if self.universal_newlines:
                    r = self._translate_newlines(r)
                return r
            finally:
                if not conn.closed:
                    fcntl.fcntl(conn, fcntl.F_SETFL, flags)

def get_output(cmd, bufsize=1, cwd=None):
    """Run command with arguments.  Wait for command to complete, then return 
    a 3-elements tuple with command stdout as the first element, command 
    stderr as the second element and the command return code as the third one.
    "cmd" is the command string to execute as you would write it in the shell
    "bufsize" is the buffer size:
        0: unbuffered
        1: line buffered
        number: positive values means use a buffer of (approximately) that size,
                a negative "bufsize" means to use the system default, which 
                usually means fully buffered
    "cwd": the command current working directory
    
    Example:
    (output, err, retcode) = get_output(["ls", "-l"])
    
    Note: In Windows, the command windows is hidden.  
    """

    # remove spaces from command and split it in a list suitable for Popen
    cmd = cmd.strip().split()

    # if we are in windows do not show the process window
    startupinfo = None
    if subprocess.mswindows:
        startupinfo = STARTUPINFO()
        startupinfo.dwFlags |= STARTF_USESHOWWINDOW
        startupinfo.dwFlags |= SW_HIDE

    process = Popen(
        cmd,
        stdout=PIPE,
        stderr=PIPE,
        stdin=PIPE,
        bufsize=bufsize,
        cwd=cwd,
        universal_newlines=True
    )
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr

