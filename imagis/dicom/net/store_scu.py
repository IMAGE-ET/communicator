# python imports
import os, sys
from string import Template

# imagis imports
import imagis.dicom.net as net
from imagis.utils.process import get_output

class StoreSCU(object):

    def __init__(self, aet='STORESCU'):
        self.aet = aet
        self._output, self.errors = '', ''

    def single_store(self, file, raet, raddress, rport=104):
        if not os.path.isfile(file):
            raise net.DicomIOError, 'file must be a real file, not a directory'

        cmd = os.path.join(
            net.DCM4CHE_BIN_DIR,
            'dcmsnd.bat' if sys.platform == 'win32' else 'dcmsnd'
        )
        tokens = {
            'cmd': cmd,
            'aet': self.aet,
            'raet': raet,
            'raddress': raddress,
            'rport': rport,
            'file': file,
        }
        cmd = Template(
            '$cmd -L $aet $raet@$raddress:$rport $file'
        ).safe_substitute(tokens)

        self._retcode, self._output, self._error = get_output(cmd, 4096)

        # check for errors
        if self._retcode == 1 or self._retcode == 2:
            raise self._get_exception()


    def statistics(self):
        lines = self._output.splitlines()
        for line in lines:
            if 'Sent' in line:
                values = line.split()
                files_sent = values[1]
                total_size = values[3][2:-1]
                total_time = values[5]
                speed = values[6][2:-1]
                return files_sent, total_size, total_time, speed
        return None

    def _get_exception(self):
        if 'skipped' in self._error:
            exception = net.DicomIOError
        elif 'server' in self._error:
            exception = net.ServerError
        elif 'Commitment' in self._error:
            exception = net.StorageCommitmentError
        elif 'association' in self._error:
            exception = net.AssociationError
        elif 'send' in self._error:
            exception = net.StoreError
        elif 'TLS' in self._error:
            exception = net.TLSContextError
        else:
            exception = net.DicomError

        return exception(self._error_message())

    def _error_message(self):
        lines = self._error.splitlines()
        for line in lines:
            if 'ERROR' in line or 'WARNING' in line:
                return ':'.join(line.split(':')[1:]).strip()
        return 'unknown error'
