'''
Created on Aug 2, 2010

@author: sackufpi
'''
import xmlrpclib
from twisted.web import xmlrpc #, server, resource, static, http
#from twisted.internet import reactor, protocol, defer
from ConfigParser import NoOptionError, NoSectionError
from dicom_network import DicomServices
from os import path
import os
#import shlex
#import pickle
#import subprocess
#import io
#import sys
#import bsddb
#import time
#import shutil

from web_services_manager import WebServicesManager

Fault = xmlrpclib.Fault

class WCFind(xmlrpc.XMLRPC):#WebServicesManager):
    '''Clase encargada de buscar en los servidores dicom locales.'''
    def __init__(self, logs_path, cfg, user='', password=''):
        #!!! WebServicesManager.__init__(self, user, password)
        self.logs_path = logs_path
        self.global_cache = path.join(logs_path, "global_search_cache")
        if not path.isdir(self.global_cache):
            os.mkdir(self.global_cache)
        xmlrpc.XMLRPC.__init__(self)
        self.allowNone = None
        self.cfg = cfg # archivo de configuracion
        self.services = DicomServices()
        self.dicom_server = cfg.get("raddress", 'localhost')
        self.port = int(cfg.get("rport", 1104))
        self.called_aet = cfg.get("raet", 'IMGSVR')
        self.local_port = int(cfg.get("lport", 3000))
        self.calling_aet = cfg.get("aet", 'any')   
        
    def xmlrpc_cfind(self, query_keys):
        print query_keys
        rsp_codes= {"find_response": 100,
                   "dicom_error": 101,
                   "service_error":102}
        dataset_dict_list = []
        try:
            try:
                self.services.connect(
                                      self.dicom_server, self.port,
                                      self.calling_aet, self.called_aet
                )
                keys_in_level, dataset_vector = self.services.cfind(query_keys)
                if dataset_vector:
                    while dataset_vector.size():
                        dataset = dataset_vector.pop()
                        dataset_dict_list.append(
                            self.services.convert_dataset_to_response(
                                        query_keys, 
                                        keys_in_level, dataset
                                    )
                            )
                
                    print dataset_dict_list
                    print "***********************************************\n"
                    print "All response: ", str(len(dataset_dict_list))
                    return [dataset_dict_list, rsp_codes["find_response"]]
                #else: error         
            except Exception, text_error:
                print text_error
                return ["Failed connect with dicom server", rsp_codes["dicom_error"]]

        except NoOptionError, textError:
            print textError
            print "Error: Check in file configuration " 
            return ["Wait some minutes for use this service.", rsp_codes["service_error"]] 
        except NoSectionError, textError:
            print textError
            print "Error: Check in file configuration " 
            return ["Wait some minutes for use this service.", rsp_codes["service_error"]]
        except Exception, textError:
            return ["Wait some minutes for use this service.", rsp_codes["service_error"]]
    
