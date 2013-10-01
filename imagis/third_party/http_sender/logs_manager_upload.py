'''
Created on Nov 9, 2009

@author: sackufpi
'''
import os
from os import path

class LogsManager(object):
    '''Registro de logs de transmision''' 
    def __init__(self):
         pass
                
    def write_log(self, lineW, filename_log):    
        try:
             line_list = lineW.split("|")
             base_name = line_list[1] + "_" + line_list[4] + '.state'
             file_log = open(filename_log + "/" + base_name, "w")
             file_log.writelines(lineW)
             file_log.close()
                          
        except IOError, textError:
                print textError     
     
    def remove_log(self, filename_log):
         if path.isfile(filename_log):
             os.remove(filename_log)
    
    def read_log(self, filename_log):
         if path.isfile(filename_log):
             file_log = open(filename_log, "r")
             line = file_log.readline()
             file_log.close()
             return line
         return ""