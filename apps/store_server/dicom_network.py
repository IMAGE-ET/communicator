#!/usr/bin/env python
# -*- coding: utf-8 -*-

#import logging
import gdcm

#logger = logging.getLogger(__name__)

class Watcher(gdcm.SimpleSubjectWatcher):
    
    def ShowProgress(self, sender, event):
        print 'x'
        
class ConnectionError(Exception):
    def __init__(self):
        self.hostname = None
        self.port = None

class AssociationError(ConnectionError):
    def __init__(self):
        self.service = None
        self.calling_aet = None
        self.called_aet = None

    
class DicomServices(object):
    
    def __init__(self):
        self.network_handler = gdcm.CompositeNetworkFunctions()
        self._service_manager = gdcm.ServiceClassUser()
                        
    def connect(self, hostname, port, calling_aet, called_aet):
        self._service_manager.SetHostname(hostname)
        self._service_manager.SetPort(port)
        self._service_manager.SetAETitle(calling_aet)
        self._service_manager.SetCalledAETitle(called_aet)
        #self._service_manager.SetTimeout(1000)
        if not self._service_manager.InitializeConnection():
                raise Exception("Failed to establish connection.")
    
    def echo(self):
        
        pre_contexts = self._get_presentation_contexts('echo')
        self._service_manager.SetPresentationContexts(pre_contexts)
        if not self._service_manager.StartAssociation():
                return False
                #raise Exception("Start Association for CEcho Failed.")  
        pcinfo_accepted = self.prescontexts_accepted(pre_contexts)
        abs_list = pcinfo_accepted[1]
        
        if '1.2.840.10008.1.1' in abs_list:
            echo_result = self._service_manager.SendEcho()
            self._service_manager.StopAssociation()
            return echo_result
        else:
            self._service_manager.StopAssociation()
            return False
#       
    def construct_query(self, model, query_level, keys, in_move = False):
        if model > 1 or model < 0:
            raise Exception("Need to explicitly choose query " + \
                            "retrieve model, " + \
                            "eStudyRootType or ePatientRootType.")

        if model == gdcm.eStudyRootType and query_level == gdcm.ePatient:
            raise Exception("Query level <ePatient> cannot be used with" + \
                            "eStudyRootType query retrieve model.")
        
        query = self.network_handler.ConstructQuery(model, query_level, \
                                                    keys, in_move)
        if not query:
            raise Exception("Query construction failed.")
        else:
            # inStrict=false the tags from the current level and all higher
            # levels are now considered valid in query
            if not query.ValidateQuery(False): 
                raise Exception("You have not constructed a valid QR query.")
        return query    
    
    def store(self, filenames):
        
        presentation_contexts = []
        abs_filenames = {}
        generator = gdcm.PresentationContextGenerator()

        for filename in filenames:
            if generator.GenerateFromFilenames((filename, )):
                presentation_context = generator.GetPresentationContexts()
                if not len(presentation_contexts):
                    presentation_contexts.extend(presentation_context)
                present = False
                for pc in presentation_contexts:
                    if presentation_context[0] == pc:
                        present = True
                        break
                if not present:        
                    presentation_contexts.extend(presentation_context)
                        
                abstract_syntax = presentation_context[0].GetAbstractSyntax()
                abs_filenames.setdefault(abstract_syntax, []).append(filename)
        
        print '-------', len(presentation_contexts)
        print '-------', len(abs_filenames)
        self._service_manager.SetPresentationContexts(presentation_contexts)
        if not self._service_manager.StartAssociation():
            raise Exception("Start Association for CStore Failed.")
        # to evaluate the presentation contexts accepted
        send_filenames = [] 
        for presentation_context in presentation_contexts:
            if self._service_manager.IsPresentationContextAccepted(
                                                    presentation_context):
                send_filenames.extend(
                        abs_filenames[presentation_context.GetAbstractSyntax()]
                )
        
        manager = self._service_manager
        sent_filenames = []
        for filename in send_filenames:
            if manager.SendStore(filename):
                sent_filenames.append(filename)
#            else:
#                logger.error('cannot sent file: {name}'.format(name=filename))
        if not self._service_manager.StopAssociation():
            raise Exception("Stop Association for CStore Failed.")
                
        return sent_filenames, list(set(filenames) - set(sent_filenames)) 
            
   
    def find(self, query_level, keys_dataset):
        """
           1- Aqui tengo que crear la lista de contextos de presentacion
           2- Asociarme (
           3- comprobar cuales fueron los contextos aceptados en la asociacion
           4- construir el query segun los contextos aceptados.
           5- enviar el query
        """
        # Building Presentation Contexts List
        pre_contexts = self._get_presentation_contexts('find')
        print '-------', len(pre_contexts)

        self._service_manager.SetPresentationContexts(pre_contexts)
        if not self._service_manager.StartAssociation():
            raise Exception("Start Association for CFind Failed.")
        
        pcinfo_accepted = self.prescontexts_accepted(pre_contexts)
        pcontexts_accepted = pcinfo_accepted[0]
        abs_list = pcinfo_accepted[1]
        
        if not len(pcontexts_accepted):
            raise Exception("Dicom Server not permit QueryRetrieve operations.")
        
        model = self.get_model('find', query_level, abs_list)        
        if model < 0 or model > 1:
            raise Exception("El modelo QR en el DCMSERVER no soporta " + \
                            "busqueda a ese nivel.")
        
        dataset_vector = gdcm.DataSetArrayType()
        query = self.construct_query(model, query_level, keys_dataset)  
        status_cfind = self._service_manager.SendFind(query, dataset_vector)
        
        if not status_cfind:
            raise Exception("Internal error in SendFind function.")
        else:
            l = dataset_vector.size()
#            while dataset_vector.size():
#                print dataset_vector.pop()
#            
            print "ALLLLLL : ", l
            return dataset_vector    

        if not self._service_manager.StopAssociation():
            raise Exception("Stop Association Failed.")        

    def move(self, query_level, keys_dataset, output_dir, lport_scp = 3000):
        """
           1- Aqui tengo que crear la lista de contextos de presentacion
           2- Asociarme 
           3- comprobar cuales fueron los contextos aceptados en la asociacion
           4- construir el query segun los contextos aceptados.
           5- enviar el query
        """
        # Always remember to define PortSCP for move
        self._service_manager.SetPortSCP(lport_scp)
        # Building Presentation Contexts List
      
        pre_contexts = self._get_presentation_contexts('move')
        print '-------', len(pre_contexts)
        self._service_manager.SetPresentationContexts(pre_contexts)
        if not self._service_manager.StartAssociation():
            raise Exception("Start Association for CMove Failed.")
        
        pcinfo_accepted = self.prescontexts_accepted(pre_contexts)
        pcontexts_accepted = pcinfo_accepted[0]
        abs_list = pcinfo_accepted[1]
                
        if not len(pcontexts_accepted):
            raise Exception("Dicom Server not permit QueryRetrieve operations.")
        
        model = self.get_model('move', query_level, abs_list)        
        if model < 0 or model > 1:
            raise Exception("El modelo QR en el DCMSERVER no soporta " + \
                            "busqueda a ese nivel.")
            
        query = self.construct_query(
            model, query_level, keys_dataset, in_move = True
        )
        status_move = self._service_manager.SendMove(query, output_dir)
        
        if not status_move:
            return False
        else:
            print "Move operation "
            return True
        
        if not self._service_manager.StopAssociation():
            raise Exception("Stop Association for CMove Failed.")        
    
    def _get_presentation_contexts(self, service, **kwargs):
        presentation_contexts = []
        generator = gdcm.PresentationContextGenerator()
        if service == 'echo':
            generator.GenerateFromUID(gdcm.UIDs.VerificationSOPClass)
            presentation_contexts.extend(generator.GetPresentationContexts())
        elif service == 'find' or service == 'move':
            if service == 'find':
                uids = (
                    gdcm.UIDs.PatientRootQueryRetrieveInformationModelFIND,
                    gdcm.UIDs.StudyRootQueryRetrieveInformationModelFIND
                )
            else:
                uids = (
                    gdcm.UIDs.PatientRootQueryRetrieveInformationModelMOVE,
                    gdcm.UIDs.StudyRootQueryRetrieveInformationModelMOVE
                )
            
            # add generated presentation contexts to the return list
            for uid in uids:
                generator.GenerateFromUID(uid)
                presentation_contexts.extend(
                    generator.GetPresentationContexts()
                )    
                    
        elif service == 'store':
            filenames = kwargs.get('filenames')
            if filenames:    
                if generator.GenerateFromFilenames(filenames):
                    presentation_contexts.extend(
                        generator.GetPresentationContexts()
                    )

        return presentation_contexts
       
    def get_model(self, service, query_level, abs_list):
        
        model = -1
        patientroot_model_find_uid = '1.2.840.10008.5.1.4.1.2.1.1'
        patientroot_model_move_uid = '1.2.840.10008.5.1.4.1.2.1.2'
        studyroot_model_find_uid = '1.2.840.10008.5.1.4.1.2.2.1'
        studyroot_model_move_uid = '1.2.840.10008.5.1.4.1.2.2.2'
        
        patientroot_accepted = False
        studyroot_accepted = False
         
        if service == 'move' or service == 'find':
            if service == 'move':
                if studyroot_model_find_uid in abs_list and \
                        studyroot_model_move_uid in abs_list:
                    studyroot_accepted = True
                if patientroot_model_find_uid in abs_list and \
                        patientroot_model_move_uid in abs_list:
                    patientroot_accepted = True
            elif service == 'find':
                if studyroot_model_find_uid in abs_list:
                    studyroot_accepted = True
                if patientroot_model_find_uid in abs_list:
                    patientroot_accepted = True    
                
            if not query_level == gdcm.ePatient and studyroot_accepted:
                model = gdcm.eStudyRootType
            elif query_level == gdcm.ePatient and patientroot_accepted:
                model = gdcm.ePatientRootType
            elif not studyroot_accepted and patientroot_accepted:    
                model = gdcm.ePatientRootType
        
        return model
       
    def prescontexts_accepted(self, pre_contexts):
        '''Esta funcion retorna una tupla con la lista de contextos
         de presentacion aceptados y la lisa de Abstract Syntax pertenecientes
         a estos contextos.'''
        pcontexts_accepted = []
        abs_list = []
        for pc in pre_contexts:
            if self._service_manager.IsPresentationContextAccepted(pc):
                pcontexts_accepted.append(pc)
                abs_list.append(pc.GetAbstractSyntax()) 
        return (pcontexts_accepted, abs_list)
    
    def get_keys_in_level(self, dic_keys):
        # Estos diccionarios pueden estar en ficheros
        level_study = {
                        "StudyDescription": (0x0008,0x1030),
                        "StudyDate": (0x0008,0x0020),
                        "StudyTime": (0x0008,0x0030),
                        "StudyInstanceUID": (0x0020,0x000D),
                        "NumberStudyRelatedInstances": (0x0020,0x1208),
                        "PatientName": (0x0010,0x0010),
                        "PatientID": (0x0010,0x0020),
                        "PatientSex": (0x0010,0x0040),
                        "PatientAge": (0x0010,0x1010),
                        "PatientBirthDate": (0x0010,0x0030),
                        "ModalitiesinStudy": (0x0008,0x0061),
        }
                
        level_series = {
                        "SeriesInstanceUID": (0x0020,0x000E),
                        "Modality": (0x0008,0x0060),
                        "SeriesDate": (0x0008,0x0021),
                        "SeriesTime": (0x0008,0x0031),
                        "NumberSeriesRelatedInstances": (0x0020,0x1209) 
        }
        
        level_image = {
                       "SopInstanceUID": (0x0008,0x0018),
                       "InstanceNumber": (0x0020,0x0013),
                       "SopClassUID": (0x0008,0x0016)
        }
        
        all_literal_key = {}
        all_literal_key.update(level_study)
        all_literal_key.update(level_series)
        all_literal_key.update(level_image) 
        study_keys_query = {}
        series_keys_query = {}
        image_key_query = {}
        all_key = {} 
        for k in dic_keys:
            if k in level_study:
                study_keys_query[level_study[k]] = dic_keys[k]
            elif k in level_series:
                series_keys_query[level_series[k]] = dic_keys[k]
            elif k in level_image:
                series_keys_query[level_series[k]] = dic_keys[k]    

        for k in study_keys_query:
            series_keys_query[k] = ''
        keys_in_level = {}        
        keys_in_level['study'] = study_keys_query
        keys_in_level['series'] = series_keys_query
        keys_in_level['image'] = image_key_query
        all_key.update(keys_in_level['study'])
        all_key.update(keys_in_level['series'])
        all_key.update(keys_in_level['image'])
        keys_in_level['all_key'] = all_key
        keys_in_level['all_literal_key'] = all_literal_key
        
        return keys_in_level
         
    
    def cfind1(self, dic_keys):
        keys_in_level = self.get_keys_in_level(dic_keys)
        query_dataset = self.construct_dataset(keys_in_level['all_key'])
        datasets_result = self.find(gdcm.eSeries, query_dataset)
        return datasets_result
    
    def cfind(self, dic_keys):
        # Esta funcion hay que reimplementarla completamente 
        # Solo funciona para las consulta hechas dede la interfaz grafica 
        # no es para todo tipo de consulta
        datasets_study_resut = gdcm.DataSetArrayType()
        datasets_series_resut = gdcm.DataSetArrayType()
#        datasets_image_resut = gdcm.DataSetArrayType()
        
        keys_in_level = self.get_keys_in_level(dic_keys)
        
        cochinaa = False
        for key in keys_in_level['study']:
            if keys_in_level['study'][key]:
                cochinaa = True
                break
                
        if cochinaa:
            query_dataset = self.construct_dataset(keys_in_level['study'])
            datasets_study_resut = self.find(gdcm.eStudy, query_dataset)
#            while datasets_study_resut.size():
#                print datasets_study_resut.pop() 
            while datasets_study_resut.size():
                dataset = datasets_study_resut.pop()
                if keys_in_level['series']:
                    
                    query_dataset = self.construct_dataset(
                                                keys_in_level['series'],
                                                dataset
                                    )
                    self._service_manager.InitializeConnection()
                    datasets_vector_result = self.find(
                                                gdcm.eSeries, query_dataset
                                            )
                    while datasets_vector_result.size():
                        datasets_series_resut.append(
                                                    datasets_vector_result.pop()
                                            )
            if datasets_series_resut.size():
                #OJOO con esta modificacion --> return datasets_series_result era lo que estaba
                return (keys_in_level, datasets_series_resut)
            else: 
                return None
        else:
            query_dataset = self.construct_dataset(keys_in_level['all_key'])
            datasets_result = self.find(gdcm.eSeries, query_dataset)
            return (keys_in_level, datasets_result)         
                        
#                    while datasets_series_resut.size():
#                        dataset = datasets_series_resut.pop()
#                        if keys_in_level['image']:
#                            query_dataset = self.construct_dataset(
#                                                        keys_in_level['image'],
#                                                        dataset
#                                            )
#                            self._service_manager.InitializeConnection()
#                            datasets_vector_result = self.find(
#                                                        gdcm.eImageOrFrame,
#                                                        query_dataset
#                                                    )
#                        while datasets_vector_result.size():
#                            datasets_image_resut.append(
#                                                   datasets_vector_result.pop()
#                                                )
#        if datasets_image_resut.size():
#            return datasets_image_resut
#        elif datasets_series_resut.size():
#            return datasets_series_resut

    def convert_dataset_to_dic(self, dic_keys={}, dataset=None):
        if dataset:
            for tags in dic_keys:
                group = tags[0]
                element = tags[1]
                de = dataset.GetDataElement(gdcm.Tag(group, element))
                value = str(de.GetByteValue())
                dic_keys[tags] = value
                
        return dic_keys
    
    def convert_dataset_to_response(self, query_keys, keys_in_level={}, dataset=None):
        query_keys_result = {}
        if dataset and keys_in_level and query_keys:
            for literal_key in query_keys:
                tags = keys_in_level["all_literal_key"][literal_key] 
                group = tags[0]
                element = tags[1]
                de = dataset.GetDataElement(gdcm.Tag(group, element))
                value = de.GetByteValue()
                if value:
                    query_keys_result[literal_key] = str(value)
                else:
                    query_keys_result[literal_key] = ''
        return query_keys_result
            
    def construct_dataset(self, dic_keys, dataset_rsp=None):
        #fill dataset
        dataset = gdcm.DataSet()
        for tags in dic_keys:
            group = tags[0]
            element = tags[1]
            de = gdcm.DataElement(gdcm.Tag(group, element))
            if dataset_rsp and group == 0x0020 and element == 0x000D:
                de = dataset_rsp.GetDataElement(gdcm.Tag(group, element))
                value = str(de.GetByteValue())
            else:
                value = dic_keys[tags]
            if value:
                value_length = len(value)
                de.SetByteValue(value, gdcm.VL(value_length))
                #de.SetVR(gdcm.VR(gdcm.VR.PN))
            dataset.Insert(de)
           
        return dataset
            
    def get_query_and_level(self, dic_keys):
        """Esta funcion retorna un dataset con los maching key y return key y 
        el nivel de consulta QR"""
        # Estos diccionarios pueden estar en ficheros
        level_patient = {
                         "PatientName": (0x0010,0x0010),
                         "PatientID": (0x0010,0x0020),
                         "PatientSex": (0x0010,0x0040),
                         "PatientAge": (0x0010,0x1010),
                         "PatientBirthDate": (0010,0030)
                         } 

        level_study = {
                       "StudyDescription": (0x0008,0x1030),
                       "StudyDate": (0x0008,0x0020),
                       "StudyTime": (0x0008,0x0030),
                       "StudyInstanceUID": (0x0020,0x000D),
                       "NumberStudyRelatedInstances": (0x0020,0x1208) 
                       }
                
        level_series = {
                        "SeriesInstanceUID": (0x0020,0x000E),
                        "Modality": (0x0008,0x0060),
                        "SeriesDate": (0x0008,0x0021),
                        "SeriesTime": (0x0008,0x0031),
                        "NumberSeriesRelatedInstances": (0x0020,0x1209) 
                        }
        
        level_image = {
                       "SopInstanceUID": (0x0008,0x0018),
                       "InstanceNumber": (0x0020,0x0013),
                       "SopClassUID": (0x0008,0x0016)
                       }
        
        alias_tags = {}
        alias_tags.update(level_patient)
        alias_tags.update(level_study)
        alias_tags.update(level_series)
        alias_tags.update(level_image)
        
        query_level = -1

        for attr_key in dic_keys:
            value = dic_keys[attr_key]
            if attr_key in level_image:
                if value: 
                    query_level = gdcm.eImageOrFrame
                break
            elif attr_key in level_patient:
                if value and query_level < gdcm.ePatient:
                    query_level = gdcm.ePatient
            elif attr_key in level_study:
                if value and query_level < gdcm.eStudy:
                    query_level = gdcm.eStudy   
            elif attr_key in level_series:
                if value and query_level < gdcm.eSeries: 
                    query_level = gdcm.eSeries
            else:
                raise Exception("Invaliud Tag")
        
        keys_dataset = gdcm.DataSet()
        #fill dataset
        for attr_key in dic_keys:
            group = alias_tags[attr_key][0]
            element = alias_tags[attr_key][1]
            de = gdcm.DataElement(gdcm.Tag(group, element))
            value = dic_keys[attr_key]
            if value:
                value_length = len(value)
                de.SetByteValue(value, gdcm.VL(value_length))
                #de.SetVR(gdcm.VR(gdcm.VR.PN))
            keys_dataset.Insert(de) 
                   
        return (query_level, keys_dataset)
        
        
        
if __name__ == '__main__':
    #logger.error('zzzz')
    hostname = "localhost"
    calling_aet = "any"
    called_aet = "IMGSVR"
    port = 1104
    lport_scp = 3000
    output_dir = "/home/sackufpi/Delete"
    services = DicomServices()
    w = Watcher(services._service_manager, 'Watch')
    services.connect(hostname, port, calling_aet, called_aet)
#    print services.echo()
#    services.connect(hostname, port, calling_aet, called_aet)

    #C-FIND TEST
    dic_keys = {
                "ModalitiesinStudy":'', "Modality": '', "PatientName":'', "PatientID":'',
                "PatientBirthDate":'', "StudyDate":'',
                "StudyTime":'', "StudyInstanceUID":'', "StudyDescription":'',
                "SeriesInstanceUID":''
                }
    
    dataset_vector = services.cfind(dic_keys)
    print "###################################################"
    s = dataset_vector.size()
    while dataset_vector.size():
        print dataset_vector.pop()
    print "ALL: ", str(s)         
#    query_level, keys_dataset = services.construct_dataset(dic_keys)
#    services.find(query_level, keys_dataset)
    
    #C-MOVE TEST
#    dic_keys = {
#                "PatientID": 'M7-2039', "StudyInstanceUID":
#                '1.3.12.2.1107.5.1.4.54181.30000007051701313323400000028',
#                "SeriesInstanceUID": 
#                '1.3.12.2.1107.5.1.4.54181.30050007051622175000600000054'
#                }
#    dic_keys = {
#                'StudyInstanceUID': "1.2.840.113619.2.25.1.1762306543.872805107.131", 
#                'SeriesInstanceUID': "1.2.840.113619.2.25.1.1762306543.872805107.135", 
#                'PatientID': "46 25 05"
#    }
#    
#    query_level, keys_dataset = services.construct_dataset(dic_keys)
#    services.move(query_level, keys_dataset, output_dir)
    
    #C-STORE TEST
#    import os
#    path = '/home/sackufpi/Documents/SACKUFPI/DICOM-TOOLS/images_all/img1'
#    filenames = filenames = [os.path.join(path, filename) for filename in \
#            os.listdir(path) if os.path.isfile(os.path.join(path, filename))]
#    print len(filenames)
#    files_sent, files_failed = services.store(filenames)
#    print "Files Tx: ", len(files_sent)
#    print "Files Failed: ", len(files_failed)
    
    