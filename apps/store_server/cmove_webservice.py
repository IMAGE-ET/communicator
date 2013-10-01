'''
Created on Oct 27, 2009

@author: sackufpi
'''
import xmlrpclib
from twisted.web import server, xmlrpc, resource, static, http
from twisted.internet import reactor, protocol, defer
from base64 import b64encode, b64decode
import os
import sys
from os import path
import io
import bsddb
import time
import shutil
import subprocess
import shlex
from web_services_manager import WebServicesManager
from dicom_network import DicomServices

Fault = xmlrpclib.Fault

class MoveFilesXMLRPC(xmlrpc.XMLRPC):#(WebServicesManager):

        def __init__(self, logs_path, cfg, www_path, move_path, user='', password=''):
            #WebServicesManager.__init__(self, user, password)
            self.logs_path = logs_path
            self.www_path = www_path
            self.move_path = move_path
            self.querys_state = None
            self.states_filename = path.join(self.logs_path, 'querys_state.db') 
            xmlrpc.XMLRPC.__init__(self)
            self.allowNone = None
            self.cfg = cfg # archivo de configuracion
            self.services = DicomServices()
            self.dicom_server = cfg.get("raddress", 'localhost')
            self.port = int(cfg.get("rport", 1104))
            self.called_aet = cfg.get("raet", 'IMGSVR')
            self.local_port = int(cfg.get("lport", 3000))
            self.calling_aet = cfg.get("aet", 'any')
            self.http_port = cfg.get("port", 80) 
            self.hostname =  os.uname()[1]#"10.30.131.70" #!!! os.uname()[1] retorna el hostname

#===============================================================================
# Esta funcion codificara el comando en una clave. Siempre se generara la 
# misma clave para el mismo comando, esa clave sera usada como nombre del fichero
# clave.db que contendra el registro de todas las imagenes pertenecientes a esa consulta.
#===============================================================================
        def query_encode(self, cmd):
            '''Esta funcion codifica el cmd en un numero entero.'''
            query_key = hash(str(cmd))
            return str(query_key)
          
        def xmlrpc_getUrls(self, cmd):
            ''' esta funcion retorna la lista de urls '''
            #              return ["http://localhost:8080/iMagis/Cerebro.mpg", \
            #                      "http://localhost:8080/iMagis/CT_4acced61b5fddb8d.dcm"]
            def url_list(query_db):
                urls = []
                for filename in query_db: #OJO --> verificar la construccion de la url 
                    url = "http://" + self.hostname + ":" + self.http_port + \
                         "/iMagis/" + str(cmd['PatientID']) + "/" + filename 
                    urls.append(url)
                query_db.close()    
                return urls
            
            '''Esta funcion comprueba si existe algun fichero de registro que
            identifique a la consulta (query_key.db), en caso afirmativo llama
             a la funcion url_list(query_file), en otro caso realiza la 
             consulta dcm move nuevamente y comprueba nuevamente la existencia
             del fichero query_key.db'''        
            def retry_query(query_file):
                while True:
                    if path.isfile(query_file):
                        query_db = bsddb.btopen(query_file, 'c')
                        return  url_list(query_db)
                    else:
                        print 'Invalid filename: ', query_file
                        #                            Mando a hacer la consulta dcm move. Esta consulta me
                        #                            copiara en la carpeta indicada los ficheros movidos
                        #                            del servidor DICOM y el fichero query_key.db
                        new_folder = path.split(query_file)[0]
                        self.dicom_move(cmd, new_folder, '')
                        return retry_query(query_file)
            
            def newMoveCMD(cmd, query_file, new_folder):
                find_cmd = ''  # hay que construir el find_cmd de acuerdo al comando cmd
                sopintans_uids = ''#self.freddy_find(find_cmd) #retorna una lista de sopinstans_uid
                if path.isfile(query_file):
                    query_db = bsddb.btopen(query_file, 'c') # es un dict
                    sopinst_nocached = list(set(sopintans_uids) ^ set(query_db))
                    #ahora mando a buscar esas imagenes que son las que no estan
                    #cacheadas, para eso tengo que construir el nuevo move cmd.
                    if sopinst_nocached:
                        new_cmd = ''#sopintans_uids[sopinst_nocached]' # hay que contruir el new_cmd
                        self.dicom_move(cmd, new_folder, new_cmd)                                
                                              
            if path.isdir(self.www_path):
                self.querys_state = bsddb.btopen(self.states_filename, 'c')
                query_key = self.query_encode(cmd)
                if 'PatientID' in cmd:
                    new_folder = path.join(self.www_path, str(cmd['PatientID']))
                    # Codifico la consulta en la llave identificadora de la consulta.
                    query_file = path.join(new_folder, query_key + '.db')
                    if path.isdir(new_folder):
            #                      Esta subrutina me posibilitara que si llega un cliente 
            #                      ordenando una consulta que ya esta en proceso, o sea que
            #                      otro cliente ordeno segundos antes la misma consulta, esta
            #                      no se ordene nuevamente sino que el ultimo cliente esperara
            #                      el resultado.                       
                        if query_key in self.querys_state:
                            if self.querys_state[query_key] == 'locked':
                                expire_time = 120 # 2 minutos maximo a esperar.
                                elapse_time = 0
                                while True:
                                    print 'Waiting one minute pending finish query.'
                                    time.sleep(60) # esperar un tiempo determinado
            #                                      Cuando la espera llegue a un valor limite
            #                                      llamar a self.dicom_move(cmd, new_folder)
            #                                      y luego a retry_query(query_file) para salir
            #                                      de ese estado infinito, asumiendo que la
            #                                      consulta anterior se perdio.
                                    if self.querys_state[query_key] == 'ready':
                                        return retry_query(query_file)
                                    else:                                                                
                                        elapse_time += 60
                                        if elapse_time == expire_time:
                                            self.querys_state.close()
                                            self.dicom_move(cmd, new_folder, '') 
                                            self.querys_state = bsddb.btopen(self.states_filename, 'c')
                                            self.querys_state[query_key] = 'ready'
                                            self.querys_state.close()
                                            
                                            return retry_query(query_file)
                            else:
                                #ya alguien realizo este mismo comando
                                #antes que yo, y no lo tengo que invocar
                                #nuevamente, las imagenes estan cacheadas
                                #pero tengo que comprobar si para este comando
                                #hay nuevas imagenes en el servidor y mandarlas a buscar. 
                                '''
                                 self.querys_state[query_key] = 'locked'
                                 self.querys_state.close()
                                 newMoveCMD(cmd, query_file, new_folder)
                                 self.querys_state = bsddb.btopen(self.states_filename, 'c')
                                 self.querys_state[query_key] = 'ready'
                                 self.querys_state.close()
                                 '''
                                return retry_query(query_file)
                        else:
                            self.querys_state[query_key] = 'locked'
                            self.querys_state.close()
                            self.dicom_move(cmd, new_folder, '')
                            self.querys_state = bsddb.btopen(self.states_filename, 'c')
                            self.querys_state[query_key] = 'ready'
                            self.querys_state.close()
                            
                            return retry_query(query_file)         
                    else: 
                        #creo el directorio de la nueva consulta
                        os.mkdir(new_folder)
                        #                            Mando a hacer la consulta dcm move. Esta consulta me
                        #                            copiara en la carpeta indicada los ficheros movidos
                        #                            del servidor DICOM y el fichero query_key.db
                        self.querys_state[query_key] = 'locked'
                        self.querys_state.close()
                        self.dicom_move(cmd, new_folder, '')
                        self.querys_state = bsddb.btopen(self.states_filename, 'c')
                        self.querys_state[query_key] = 'ready'
                        self.querys_state.close()
                        
                        return retry_query(query_file)
            else:
                print "Invalid directory ", self.www_path              
                            

        def dicom_move(self, cmd, new_folder, new_cmd):
            query_key = self.query_encode(cmd)
            query_file = path.join(new_folder, query_key + '.db')
#            self.querys_state = bsddb.btopen(self.states_filename, 'c')
#            self.querys_state[query_key] = 'locked'
#            self.querys_state.close()
            # Esta operacion puede demorar minutos.
            if new_cmd:
                cmd = new_cmd
            filenames = self.cmove(cmd)
            query_db = bsddb.btopen(query_file, 'c')
            for filename in filenames:
                name = path.basename(filename)
                local_filename = path.join(new_folder, name)
                if path.isfile(local_filename):
                    os.remove(filename) # ya esta cacheado
                else:
                    shutil.move(filename, new_folder)
                query_db[name] = 'ready'
            
            query_db.close()
#            self.querys_state = bsddb.btopen(self.states_filename, 'c')
#            self.querys_state[query_key] = 'ready'
#            self.querys_state.close()
                
            
        def cmove(self, cmd):
            query_level, keys_dataset = self.services.get_query_and_level(cmd)
           
            self.services.connect(
                                  self.dicom_server, self.port,
                                  self.calling_aet, self.called_aet
            )
            #self.output_dir = tempfile.mkdtemp(prefix='imagis_')
            #self.output_dir_list.append(self.output_dir)
            if self.services.move(
                               query_level, keys_dataset,
                               self.move_path, lport_scp = self.local_port):
                        
                filenames = self.createFileNameList(self.move_path)
                return filenames
            else:
                pass # MANEJAR POR QUE EL MOVE NO SE REALIZO.                         

        def freddy_find(self, cmd):
            '''Hay que hace un dicom find para con este resultado saber que
             imagenes estan cacheadas y cuales no para hacer un move y mandarlas a buscar'''
            
            def dcmfind_parser(filename):
                tags_table = {"Patient_ID": "(0010,0020)",
                              "Study_Instance_UID": "(0020,000D)",
                              "Series_Instance_UID": "(0020,000E)",
                              "SOP_Instance_UID": "(0008,0018)"}
                f = open(filename)
                SopInstansUID_list = []
                for l in f.readlines():
                    lst = l.split()
                    if len(lst):
                        if lst[0] == tags_table["SOP_Instance_UID"]:
                            if lst[3]:
                                SopInstansUID_list.append(lst[3][1:len(lst[3])-1])     #sin los corchetes           
                return SopInstansUID_list
                            
            tools_path = path.join(os.getcwd(), 'dcm4che2')
            tools_path = path.join(tools_path, 'bin')
            # tengo que definir un archivo de configuracion para el cliente
            if sys.platform == 'win32':
                a = 'sd'
            elif sys.platform == 'linux2':
                dcm_cmd = tools_path + "/dcmqr ISERVER@localhost:2000 -I -q 00100020=07-6314 " + \
                "-q 0020000D=1.2.392.200036.9110.167138003.3361.20070904114115.0 -q 0020000E=1.2.392.200036.9110.167138003.2.20070904114237.0 -r 00080018"
                args = shlex.split(dcm_cmd) 
                p = subprocess.Popen(args)
                sts = os.waitpid(p.pid, 0)[1] # sts es el estado de finalizacion del proceso dcmqr
            
            SopInstansUID_list = dcmfind_parser('/home/sackufpi/out.txt')    
            return SopInstansUID_list
        
        def createFileNameList(self, filename):
            ''' Esta funcion es para probar.'''
            try:
                filenames_moved = []
                if path.isdir(filename):
                    for root, dirs, files in os.walk(filename):
                        for name in files:
                            filename_moved = path.join(root, name)
                            filenames_moved.append(filename_moved)
                else:
                    print "Invaliud directory or access deny exist: " + filename
                    return None
                return filenames_moved
            except IOError, textError:
                print textError
                                                                              
   
        









