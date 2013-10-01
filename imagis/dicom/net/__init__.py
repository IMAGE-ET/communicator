# python imports
import os

# imagis imports
import imagis

DCM4CHE_BIN_DIR = os.path.join(imagis.THIRD_PARTY_DIR, 'dcm4che', 'bin')

# custom exceptions
class DicomError(Exception):
    def __init__(self, error_msg):
        self.error_msg = error_msg
        
    def __str__(self):
        return repr(self.error_msg)
    
class TLSContextError(DicomError):
    pass

class ServerError(DicomError):
    pass

class AssociationError(DicomError):
    pass

class StorageCommitmentError(DicomError):
    pass

class DicomIOError(DicomError):
    pass

class StoreError(Exception):
    pass
