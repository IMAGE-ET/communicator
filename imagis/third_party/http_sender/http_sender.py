'''
Created on Jul 2, 2009

@author: sackufpi
'''


###*****************XMLRPC ASINC PINCHA ************************************

#! /usr/bin/python
# -*- coding: utf-8 -*-
from urlparse import urlparse, urljoin
import twisted.web.xmlrpc as xmlrpc
from twisted.internet import reactor
from twisted.internet import defer
from twisted.web import xmlrpc
from base64 import b64encode, b64decode
from twisted.python import usage
from proxied import ProxiedXMLRPC
from logs_manager_upload import LogsManager
import xmlrpclib
import sys
import base64
import io
import os
from os import path
import string


class XMLRPC_ClientDcmFiles:
    def __init__(self, URL, fileNameError, listDcmTxFileNames, sizeBuffer \
                 , retryTx, verbose, time_retryTx, retransmission, \
                 http_proxy_server, http_proxy_user, http_proxy_password, http_server_user, http_server_password):
        self.URL = URL
        self.scheduleFileName = fileNameError
        self.scheduleRegisterFileNameTx = path.join(fileNameError, "schedule_Register_fileTx.log")
        self.listDcmTxFileNames = listDcmTxFileNames
        self.sizeBuffer = sizeBuffer # 80kb
        self.time_retryTx = time_retryTx
        self.numErrorTx = retryTx # numero de reintentos permitidos de la transmision por errores
        self.verbose = verbose
        self.retransmission = retransmission
        self.cant_images = 0
        self.filesystem_encoding = self.getfilesystemencoding()
        self.http_proxy_server = http_proxy_server
        self.http_proxy_user = http_proxy_user
        self.http_proxy_passwd = http_proxy_password
        self.http_server_user = http_server_user
        self.http_server_passwd = http_server_password

    def connect(self):
        try:

            if self.http_proxy_server:
                 try:
                     proxy_host, prx_port = string.split(self.http_proxy_server, ":")
                     proxy_port = int(prx_port)
                     print "Connecting to http proxy " + proxy_host + ":" + prx_port + " ..."
                     self.proxyClient = ProxiedXMLRPC(reactor, self.URL, \
                       proxy_host, proxy_port, self.http_server_user, \
                       self.http_server_passwd, http_proxy_user=\
                       self.http_proxy_user, http_proxy_passwd=self.http_proxy_passwd)
                     self.sendFiles()
                 except ValueError:
                         print "Bad http proxy address. The http proxy configuration is: Ex, Hostname:Port or IPAddress:Port"
                         #reactor.stop()
            else:
                 print "Connecting to " + self.URL + " ..."
                 self.proxyClient = xmlrpc.Proxy(self.URL, user=self.http_server_user, password=self.http_server_passwd)
                 self.sendFiles()

        except Exception, textError:
            print "Error connecting: ", textError
            #reactor.stop()

    def transferFile(self, fileName, fileNameW, pos_To_ReadWrite, numBytesToRead):
         if path.isfile(fileName) == True:
                   self.fileR = open(fileName, "rb")
                   print '\n\nSending: %s' % fileName
                   self.TransferFileBuffered(fileNameW, pos_To_ReadWrite, numBytesToRead)
         else:
               print "Invalid fileName: " + fileName
               if len(self.listDcmTxFileNames) > 0:
                   self.sendFiles()
               else:
                    self.stopReactor()


    def sendFiles(self):
         if len(self.listDcmTxFileNames) > 0:
            numBytesToRead = self.sizeBuffer
            pos_To_ReadWrite = 0

            try:
                if self.retransmission != True:
                     fileName = self.listDcmTxFileNames.pop(0) # usando lista como una cola
                     self.sizeFile = str(path.getsize(fileName))
                     self.cant_images = self.cant_images + 1
                     print "Num-Tx:" + str(self.cant_images)
                     self.filename_tx = path.basename(fileName)
                     filename_log = path.join(self.scheduleFileName, self.filename_tx) \
                                     + "_" + self.sizeFile + ".state"
                     line = LogsManager().read_log(filename_log)
                     line_list = []
                     if line != "":
                          line_list = line.split("|")
                          if len(line_list) > 0:
                               fileNameW = line_list[2]
                               pos_To_ReadWrite = line_list[3]
                               self.transferFile(fileName, fileNameW, pos_To_ReadWrite, numBytesToRead)
                     else:
                          self.transferFile(fileName, self.filename_tx, pos_To_ReadWrite, numBytesToRead)
                else:
                     dataTxfile = self.listDcmTxFileNames.pop(0) # usando lista como una cola 
                     fileName = dataTxfile[0]
                     self.filename_tx = path.basename(fileName)
                     self.sizeFile = str(path.getsize(fileName))
                     fileNameW = dataTxfile[1]
                     pos_To_ReadWrite = dataTxfile[2]
                     self.transferFile(fileName, fileNameW, pos_To_ReadWrite, numBytesToRead)

            except IOError as detail:
                     print detail
         else:
              self.stopReactor()

    def TransferFileBuffered(self, FileName, posToRead, numBytesToRead):
        ''''  Leer un archivo completo usando un buffer '''
        try:
            self.fileR.seek(int(posToRead))
            data = self.fileR.read(numBytesToRead)
            buffer = xmlrpclib.Binary(data)
            #buffer = b64encode(self.fileR.read(numBytesToRead))
            posToWrite = int(posToRead)
            try:
                #print '\n\nSending: %s' % FileName
#                fileName = FileName
                fileName = unicode(FileName, self.filesystem_encoding)
                dataRW = (fileName, posToRead, numBytesToRead, self.numErrorTx)

                d = self.proxyClient.callRemote('WriteBufferFile',
                                                fileName, buffer, posToWrite)
                d.addCallbacks(self.ReadWriteBufferFile, self.ErrorHandler,
                               "", "", dataRW)

            except Exception as detail:
                    print "Error calling remote method1: ", detail
        except IOError as detail:
                    print "ERROR READING: ", detail


    def ErrorHandler(self, error, *dataRW, **kwargs):

        print "Error callRemote: ", error
        numErrorTx = dataRW[3] - 1
        print "numErrorTx = ", numErrorTx
        dataRW_Err = (dataRW[0], dataRW[1], dataRW[2], numErrorTx)
        try:
            ''' Aqui programare para que en 30 segundos se reanude la transmision. !!! '''
            print "The transmition will be reanude in 20 seg with 80 kb..."
            for val in dataRW_Err:
                    print val
            if numErrorTx > 0:
                reactor.callLater(self.time_retryTx, self.ReadWriteBufferFile, dataRW_Err)
            else:
                  fileName = dataRW[0].encode(self.filesystem_encoding)
                  posToWrite = int(dataRW[1])
                  lineW = self.URL + "|" + self.filename_tx + "|" + fileName + "|" \
                            + str(posToWrite) + "|" + self.sizeFile
                  LogsManager().write_log(lineW, self.scheduleFileName)
                  if len(self.listDcmTxFileNames) > 0:
                       self.sendFiles()
                  else:
                       self.stopReactor()

        except Exception as detail:
                print detail

    def getfilesystemencoding(self):
          filesystem_encoding = sys.getfilesystemencoding()
          if filesystem_encoding is None:
              filesystem_encoding = sys.getdefaultencoding()
          return filesystem_encoding

    def writeLineTaskFile(self, scheduleFile, dataRW_Err):

        print type(dataRW_Err[0])
        fileName = dataRW_Err[0].encode(self.filesystem_encoding)
        print fileName

        try:
            existLine = False
            indexInit = -1
            lines = scheduleFile.readlines()
            for line in lines:
                indexInit = string.find(line, fileName)
                if indexInit != -1:
                    existLine = True
                    print "Exist one register schedule Task for file: " + fileName
                    break
            if existLine == False:
                lineW = self.URL + "|" + dataRW_Err[0] + "|" + str(dataRW_Err[1]) + "|" \
                            + str(dataRW_Err[2]) + "\n"
                print "schedule  :", lineW
                scheduleFile.write(lineW.encode(self.filesystem_encoding))
                scheduleFile.flush()

        except IOError as detail:
                    print detail
        finally:
                scheduleFile.close()

    def stopReactor(self):
        reactor.stop()

    def ReadWriteBufferFile(self, dataRW_ACK, *args, **kwargs):
        print "Writing..."
        fileName = dataRW_ACK[0].encode(self.filesystem_encoding)
        posToRead = int(dataRW_ACK[1])
        posToWrite = posToRead
        numByteToWrite = dataRW_ACK[2]
        if numByteToWrite > 0:
            try:
                self.fileR.seek(posToRead)
                bufferR = self.fileR.read(numByteToWrite)
                #buffer = b64encode(bufferR)
                buffer = xmlrpclib.Binary(bufferR)
                print "len(buf) = " + str(numByteToWrite) + " pos = " + str(posToWrite) + '\n'
                if buffer != '':
                    try:
                        lineW = self.URL + "|" + self.filename_tx + "|" + fileName + "|" \
                            + str(posToWrite) + "|" + self.sizeFile

                        LogsManager().write_log(lineW, self.scheduleFileName)

                        self.proxyClient.callRemote('WriteBufferFile',
                        fileName, buffer, posToWrite).addCallbacks(self.ReadWriteBufferFile, self.ErrorHandler, "", "", dataRW_ACK)

                    except Exception as detail:
                                print "Error calling remote method: ", detail

                else:
                     filename_log = path.join(self.scheduleFileName, self.filename_tx) \
                                     + "_" + self.sizeFile + ".state"
                     if path.isfile(filename_log):
                         os.remove(filename_log)
                     print "File: " + fileName + " transmited. " + "Total bytes transmited: " + self.sizeFile + " bytes"
                     self.fileR.close() # cierro el flujo del archivo enviado.
                     #ARREGLAR LA LLAMADA DE ABAJO.
                     print "Registering " + fileName
                     self.proxyClient.callRemote('RegisterFile_Transmited', fileName).addCallbacks(self.RegisterFileTx, self.ErrorRegisterFileTx, (fileName,), "", (fileName,))

            except IOError:
                    print "ERROR READING.!"

        else:
              ''' Aqui programare para que en 30 segundos se reanude la transmision. !!! '''
              print "The transmition will be reanude in 2 seg with 80 kb..."
              dataRW_ACK_1 = (fileName, posToRead, 81920) # 80 kb
              reactor.callLater(self.time_retryTx, self.ReadWriteBufferFile, dataRW_ACK_1)


    def RegisterFileTx(self, file_Registered, *tupleWithFileName):
        if file_Registered == "":
           self.ErrorRegisterFileTx("IOError: registering in server.", tupleWithFileName)
        else:
             print "File: " + file_Registered + " registered in server."
             self.sendFiles()


    #############    

    def ErrorRegisterFileTx(self, errorRegFileTx, *tupleWithFileName):
        print errorRegFileTx
#        try:
#            scheduleRegisterFileTx = open(self.scheduleRegisterFileNameTx, "a+")
#            name = tupleWithFileName[0][0]
#            scheduleRegisterFileTx.write(self.URL + "|" + name + "\n")
#            scheduleRegisterFileTx.flush()
#            scheduleRegisterFileTx.close()
#            self.sendFiles()
#        except IOError as detail:
#                                   print detail
#
#        finally:
#                scheduleRegisterFileTx.close()


###################################### Options #################################

#########################################           


def option_factory():
    options = [
               ["url", "U", "http://127.0.0.1:8080", "Address url to connect."],
               ["filename", "f", None, 'Filename to read files.'],
               ["logs", "l", None, 'Filename to save logs.'],
               ["size-buffer", "b", 8192, 'size buffer.', int], #8 kb default
               ["retry-tx", "r", 4, 'count retry transmission for errors.', int],
               ["time-retry", "t", 5, 'time in second between retry transmission', int],
#               ["http-proxy", "P", None, 'proxy server'],
#               ["user", "u", None, 'User name'],
#               ["password", "p", None, 'Password']
               ["http_proxy_server", "P", None, 'proxy server.'],
               ["http_proxy_user", "g", "", 'user for proxy server'],
               ["http_proxy_password", "x", "", 'password for proxy server'],
               ["http_server_user", "u", "", 'User name, origen web service.'],
               ["http_server_password", "p", "", 'Password, origen web service.']
#               ["aet", "A", None, 'Application entity title']
              ]
    return options


class xmlrpcClientOptions(usage.Options):

       optParameters = option_factory()
       optFlags = [["verbose", "V", 'verbose mode.'],
                   #["transmission","T",'Transmission mode.'],
                   ["retransmission", "R", 'Retransmission mode.']
                  ]

def createFileNameList(fileName):
    try:
        listDcmTxFileNames = []
        if path.isdir(fileName):
            for root, dirs, files in os.walk(fileName):
                for name in files:
                     listDcmTxFileNames.append(path.join(root, name))
        else:
             print "Invaliud directory or access deny exist: " + fileName
             return None
        return listDcmTxFileNames
    except IOError, textError:
                             print textError


def createFileNameListError(url , fileNameErrorFiles, fileNameTxFile):
     try:
        listDcmTxFileNames = []
        list_log = []
        if path.isdir(fileNameErrorFiles):
            for root, dirs, files in os.walk(fileNameErrorFiles):
                for basename in files:
                     name, ext = path.splitext(basename)
                     if ext == '.state':
                         filename_log = path.join(root, basename)
                         line = LogsManager().read_log(filename_log)
                         line_list = []
                         if line != "":
                              line_list = line.split("|")
                              if len(line_list) > 0:
                                   url_R = line_list[0]
                                   if url == url_R:
                                       list_log.append(line_list)

            if len(list_log) > 0:
                if path.isfile(fileNameTxFile):
                    fileNameTxFile = path.split(fileNameTxFile)[0]
                for root, dirs, files in os.walk(fileNameTxFile):
                    for basename in files:
                         for listl in list_log:
                              name = listl[1]
                              if basename == name:
                                  size_file = int(listl[4])
                                  if size_file == path.getsize(path.join(root, basename)):
                                      dataR = [path.join(root, basename), listl[2], listl[3]]
                                      listDcmTxFileNames.append(dataR)

        else:
             print "Invaliud directory or access deny exist: " + fileName
             return None
        return listDcmTxFileNames
     except IOError, textError:
                             print textError


##############
def urlParse(url):
    _url = urlparse(url, 'http')
    if _url.scheme != "http":
        return ''
    if _url.netloc:
        _url = urljoin(url, 'XMLRPC')#'SOAP')
    else:
         return ''

    return _url

##############

def parseOptionAndExecute(lCommandToParse, options):
    if len(lCommandToParse) == 1:
        options.parseOptions(['--help'])
    else:
        try:
            options.parseOptions()
            if options['filename'] and options['logs']:
                fileNameTxFile = options['filename']
                fileNameErrorFiles = options['logs']
                # Comprobar formato de la URL
                URL = urlParse(options['url'])
                if URL != '':
                    verbose = False
                    sizeBuffer = None
                    retryTx = None
                    time_retryTx = None
#                    http_proxy_server = None
#                    http_proxy_user = None
#                    http_proxy_password = None
#                    http_server_user = None
#                    http_server_password = None

                    if "verbose" in options:
                         verbose = True
                    if "size-buffer" in options:
                         sizeBuffer = options["size-buffer"]
                         if sizeBuffer <= 0:
                             raise usage.UsageError, "Is obligatory to input number size-buffer > 0."
                    if "retry-tx" in options:
                         retryTx = options["retry-tx"]
                         if retryTx <= 0:
                             raise usage.UsageError, "Is obligatory to input number retry-tx > 0."
                    if "time-retry" in options:
                         time_retryTx = options["time-retry"]
                         if time_retryTx < 0:
                             raise usage.UsageError, "Is obligatory to input number time-retry >= 0."
                    if "http_proxy_server" in options:
                         http_proxy_server = options["http_proxy_server"]

                    if "http_proxy_user" in options:
                        http_proxy_user = options["http_proxy_user"]

                    if "http_proxy_password" in options:
                        http_proxy_password = options["http_proxy_password"]

                    if "http_server_user" in options:
                         http_server_user = options["http_server_user"]
                    if "http_server_password" in options:
                         http_server_password = options["http_server_password"]

                    if path.isdir(fileNameErrorFiles):
                        if path.isfile(fileNameTxFile) or path.isdir(fileNameTxFile):
                            if path.isfile(fileNameTxFile):
                                listDcmTxFileNames = []

                                if options["retransmission"]:
                                    listDcmTxFileNames = createFileNameListError(URL, fileNameErrorFiles, fileNameTxFile)
                                    print listDcmTxFileNames
                                    if listDcmTxFileNames:
                                        xmlrpcClient = XMLRPC_ClientDcmFiles(URL, fileNameErrorFiles, listDcmTxFileNames, sizeBuffer, retryTx, verbose, time_retryTx, True, http_proxy_server, http_proxy_user, http_proxy_password, http_server_user, http_server_password)
                                        xmlrpcClient.connect()
                                        reactor.run()
                                else:
                                     listDcmTxFileNames.append(fileNameTxFile)
                                     xmlrpcClient = XMLRPC_ClientDcmFiles(URL, fileNameErrorFiles, listDcmTxFileNames, sizeBuffer, retryTx, verbose, time_retryTx, False, http_proxy_server, http_proxy_user, http_proxy_password, http_server_user, http_server_password)
                                     xmlrpcClient.connect()
                                     reactor.run()
                            else:
                                 if path.isdir(fileNameTxFile):
                                     if options["retransmission"]:
                                         # retransmitir lo que esta en los ficheros de logs
                                         listDcmTxFileNames = createFileNameListError(URL, fileNameErrorFiles, fileNameTxFile)
                                         if listDcmTxFileNames:
                                              xmlrpcClient = XMLRPC_ClientDcmFiles(URL, fileNameErrorFiles, listDcmTxFileNames, sizeBuffer, retryTx, verbose, time_retryTx, True, http_proxy_server, http_proxy_user, http_proxy_password, http_server_user, http_server_password)
                                              xmlrpcClient.connect()
                                              reactor.run()

                                     else:
                                          # transmitir todos los ficheros existentes en el directorio
                                          # se puede dar opcion de extension o sea (*.exe, *.pdf)
                                          listDcmTxFileNames = createFileNameList(fileNameTxFile)
                                          print len(listDcmTxFileNames)
                                          if listDcmTxFileNames:
                                              xmlrpcClient = XMLRPC_ClientDcmFiles(URL, fileNameErrorFiles, listDcmTxFileNames, sizeBuffer, retryTx, verbose, time_retryTx, False, http_proxy_server, http_proxy_user, http_proxy_password, http_server_user, http_server_password)
                                              xmlrpcClient.connect()
                                              reactor.run()
                        else:
                             print "Invaliud filename or deny access exist: " + fileNameTxFile
                    else:
                         print "Invaliud filename for error logs: " + fileNameErrorFiles
                else:
                     print "Incorrect URL. Use Ex: http://www.hostname.com:port or http://hostname.com or switch hostname for IP address."
            else:
                 raise usage.UsageError, "Is obligatory to input the parameters --filename(or -f) and --logs(or -l)."

        except usage.UsageError, errorText:
                print errorText



def main():
    ''' metodo principal '''

    lCommandToParse = sys.argv
    options = xmlrpcClientOptions()
    parseOptionAndExecute(lCommandToParse, options)

    print "Aqui se acaba el programa."


if __name__ == '__main__':
    main()
