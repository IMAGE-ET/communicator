# -*- coding: UTF-8 -*-

# python imports
import os
import sys
import logging
import shutil

# store_server imports
from web_services_manager import WebServicesManager

# imagis imports
try:
    import config.store_server as config
except ImportError:
    class config:
        logger = {}
        server = {}
from imagis.dicom.net import DicomError
from imagis.dicom.net.store_scu import StoreSCU

logger = logging.getLogger('store_server.StoreService')

class StoreService(WebServicesManager):
    ''' Esta clase brinda servicios xmlrpc  '''

    def __init__(self, store_path, failed_files, user='', password=''):
        WebServicesManager.__init__(self, user, password)
        self.store_path = store_path
        self.failed_files = failed_files

        #verifico la codificacion de nombres de archivos del sistema.
        self.filesystem_encoding = self.getfilesystemencoding()

        self.buffer_manager = 5
        self.load = 5
        self.allowNone = None


    def xmlrpc_RegisterFile_Transmited(self, file_name):
        ''' Esta funcion registra en un fichero el file_name de un archivo
        que ha sido transmitido satisfactoriamente.'''

        try:
            aet = config.server.get('aet', 'STORESCU')
            raet = config.server.get('raet', 'STORESCP')
            raddress = config.server.get('raddress', 'localhost')
            rport = config.server.get('rport', 104)
            file_name = os.path.join(self.store_path, file_name)

            store_scu = StoreSCU(aet)
            store_scu.single_store(file_name, raet, raddress, rport)

            # remove the stored file from the spool
            if os.path.isfile(file_name):
                os.remove(file_name)
        except DicomError as e:
            logger.error(e.error_msg)
            # move the offending file to a another folder
            try:
                logger.error(
                    'moving file: %s to folder: %s'
                    % (file_name, self.failed_files)
                )
                shutil.move(file_name, self.failed_files)
            except shutil.Error as e:
                logger.error(e)
                logger.info('removing file: %s' % file_name)
                os.remove(file_name)
            except (IOError, OSError) as e:
                logger.error(e)

        return file_name

    def rename_file(self, fileName):
        '''Esta funcion retorna vacio si no existe el fichero
        de lo contrario retorna el nuevo nombre para el fichero.'''
        if os.path.isdir(self.store_path):
            while True:
                if os.path.isfile(os.path.join(self.store_path, fileName)) == False:
                    return fileName
                else:
                    #generar nombre nuevo
                    name, ext = os.path.splitext(fileName)
                    name += "1"
                    fileName = name + ext
        else:
            raise IOError()


    def getfilesystemencoding(self):
        filesystem_encoding = sys.getfilesystemencoding()
        if filesystem_encoding is None:
            filesystem_encoding = sys.getdefaultencoding()
        return filesystem_encoding

    def xmlrpc_WriteBufferFile(self, fileName, buffer, posToWrite):
        initNumErrorTx = 4
        try:
            bufferW = buffer.data #prueba Binary object
            #bufferW = b64decode(buffer)
            numBytesToWrite = len(bufferW)
            logger.info("len(buf) = " + str(numBytesToWrite) + " pos = " + str(posToWrite) + '\n')
            posToRead = posToWrite + len(bufferW)
            logger.info("Client read in pos = " + str(posToRead))
            #fileName = b64decode(FileName)
            logger.info('Writing in file: %s\n' % fileName)

            ''' Puedo simular un switch con diferentes valores de control de trafico.'''
            if self.buffer_manager < self.load:
                numBytesToWrite = 0 # 0 kb
                self.buffer_manager = self.buffer_manager + 1

            #Retorno esta tupla a modo de elaborar un pequeno protocolo
            dataRW_ACK = (fileName, posToRead, numBytesToWrite, initNumErrorTx)
            fileName_encoded = fileName.encode(self.filesystem_encoding)

            try:
                if posToWrite == 0:
                    fileName = self.rename_file(fileName_encoded)
                    dataRW_ACK = (fileName, posToRead, numBytesToWrite, initNumErrorTx)
                    fileW = open(os.path.join(self.store_path, fileName), "wb") #a+
                    fileW.close()
                # patch 2
                #size = os.path.getsize(os.path.join(self.store_path, fileName))
                #if size != posToWrite:
                #  os.remove(os.path.join(self.store_path, fileName))
                #  raise IOError, "Reset Tx file: " + fileName + " is corrupt."                
				
                # patch 1
                if os.path.getsize(os.path.join(self.store_path, fileName)) > posToWrite:
                    fileW.truncate(posToWrite)
                elif os.path.getsize(os.path.join(self.store_path, fileName)) < posToWrite:
                    os.remove(os.path.join(self.store_path, fileName))
                    raise IOError, "file " + fileName + " is corrupt"

                fileW = open(os.path.join(self.store_path, fileName), "ab+")
                fileW.seek(posToWrite, os.SEEK_CUR)                
                fileW.write(bufferW)
                fileW.flush()
                fileW.close()

            except IOError as detail:
                posToRead = 0
                dataRW_ACK = (fileName, posToRead, numBytesToWrite, initNumErrorTx)
                print "Error writing: ", detail


        except Exception as detail:
            print detail

        return dataRW_ACK

    def xmlrpc_echo(self, val):
        print val
        return val

