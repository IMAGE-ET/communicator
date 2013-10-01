"""
First of all, this is a valid python source file, so, any python code, 
put here is valid.

This configuration file is made of of sections. Sections are valid 
python sequences (dictionaries, tuples, list). So far we have two 
sections: "logger" and "tasks". 

Logger section: 
    This section is a dictionary object, here you will configure how
    log files will be generated.
    
    Keys of logger section:
        log_file: string representing the absolute path to the log 
                  file including the name.
        max_bytes: an integer representing the maximum size of the 
                   log file until rotated.
        count: an integer representing how many times the log file 
               will be rotated.
    Note: all keys are python strings
                
Ej.
    logger = {
        'log_file': '/var/log/imagis_cron.log',
        'max_bytes': 5242880, 
        'count': 5 # how many rotated files will be generated.
    }
    
Tasks section:
    This section is a composed of a list of dictionaries. Here 
    you will configure which and how tasks will be executed. 
    Every item in the list represent a task and is a python 
    dictionary just like the one in logger section (with same syntax)
    
    Keys of every task item in the list:
        task_id: string representing the unique identifier of the task.
        
        task_type: string representing the type of the task, this type could be: 
                   daytime, interval or single.
                   
        initial_delay: integer representing how long the task will wait 
                       to start working.
        
        interval: this key is only valid if you specified the task_type 
                  to be interval and represent the interval in seconds 
                  to execute the task.
                  
        day_type: this key is only valid if you specified the task_type 
                  to be daytime and the valid values are: monthdays, weekdays
                  and represent the day type to be used when specifying days. 
                  
                  monthdays: valid integer month days from 1 to 31
                  weekdays: valid integer week days from 1 to 7
                  
        days: this key is only valid if you specified the task_type 
              to be daytime and represent the day when the task will 
              be executed. If in key day_type you specified "monthdays"
              then valid days are integers from 1 to 31 and if you 
              specified weekdays then valid days are integers from 1 to 7.
        
        start_time: this key is only valid if you specified the task_type 
                    to be daytime and represent the time when the task will 
                    be executed. The value can be a tuple with this format.
                    (HH, MM), where HH and MM are in 24H format.
                     
        task_executioner: the python callable to be executed by this task.
                          You must specify this callable with the following 
                          syntax: module_name.callable
                          You can see available modules in the task directory
                          
        params: a python dictionary that specify the parameters to be passed in
                to the task callable. Keys are the parameters names and 
                values are the parameters values.
         
    
    
Ej.

    tasks = (
        {
            'task_id': 'http_sender',
            'task_type': 'interval',
            'initial_delay': 1,
            'interval': 3,
            'task_executioner': 'task_http_sender.http_send',
            'params': {
                'url': 'http://10.30.131.70:8080',
                'spool': '/home/jmrbcu/temp/transmission/sackufpi/urgent',
                'buffer': 5120 # 5kb
            },
        },
    
        {
            'task_id': 'http_sender',
            'task_type': 'daytime',
            'day_type': 'monthdays',
            'days': range(1, 32),
            'start_time': (1, 00),
            'task_executioner': 'task_http_sender.http_send',
            'params': {
                'url': 'http://10.30.131.70:8080',
                'spool': '/home/jmrbcu/temp/transmission/sackufpi/normal',
                'buffer': 5120 # 5kb
            },
        },
    
    )

"""

logger = {
    'log_file': 'C:\\iMagis\\imagis-0.4\\home\\logs\\imagis_cron.log',
    'max_bytes': 5242880,
    'count': 5,
}

tasks = [
    {
        'task_id': 'http_sender_baracoa',
        'task_type': 'interval',
        'initial_delay': 1,
        'interval': 3,
        'task_executioner': 'task_http_sender.http_send',
        'params': {
            'url': 'http://10.20.5.115:80',
            'spool': 'C:\\iMagis\\imagis-0.4\\home\\spool\\baracoa',
            'buffer': 5120 # 5kb
        },
    },
    
    {
        'task_id': 'http_sender_pediatrico',
        'task_type': 'interval',
        'initial_delay': 1,
        'interval': 3,
        'task_executioner': 'task_http_sender.http_send',
        'params': {
            'url': 'http://10.20.5.115:80',
            'spool': 'C:\\iMagis\\imagis-0.4\\home\\spool\\pediatrico',
            'buffer': 5120 # 5kb
        },
    },
    
    {
        'task_id': 'http_sender_clinico_stgo',
        'task_type': 'interval',
        'initial_delay': 2,
        'interval': 15,
        'task_executioner': 'task_http_sender.http_send',
        'params': {
            'url': 'http://10.20.5.115:80',
            'spool': 'C:\\iMagis\\imagis-0.4\\home\\spool\\clinico_stgo',
            'buffer': 5120 # 5kb
        },
    },
    
    {
        'task_id': 'http_sender_provincial_stgo',
        'task_type': 'interval',
        'initial_delay': 3,
        'interval': 15,
        'task_executioner': 'task_http_sender.http_send',
        'params': {
            'url': 'http://10.20.4.12:80',
            'spool': 'C:\\iMagis\\imagis-0.4\\home\\spool\\provincial_stgo',
            'buffer': 5120 # 5kb
        },
    },

    {
        'task_id': 'http_sender_lenin_holguin',
        'task_type': 'interval',
        'initial_delay': 4,
        'interval': 5,
        'task_executioner': 'task_http_sender.http_send',
        'params': {
            'url': 'http://201.220.196.148:80',
            'spool': 'C:\\iMagis\\imagis-0.4\\home\\spool\\lenin_holguin',
            'buffer': 5120 # 5kb
        },
    },

    {
        'task_id': 'http_sender_clinico_holguin',
        'task_type': 'interval',
        'initial_delay': 5,
        'interval': 5,
        'task_executioner': 'task_http_sender.http_send',
        'params': {
            'url': 'http://201.220.196.171:80',
            'spool': 'C:\\iMagis\\imagis-0.4\\home\\spool\\clinico_holguin',
            'buffer': 5120 # 5kb
        },
    },

    {
        'task_id': 'http_sender_pediatrico_holguin',
        'task_type': 'interval',
        'initial_delay': 6,
        'interval': 5,
        'task_executioner': 'task_http_sender.http_send',
        'params': {
            'url': 'http://201.220.196.156:80',
            'spool': 'C:\\iMagis\\imagis-0.4\\home\\spool\\pediatrico_holguin',
            'buffer': 5120 # 5kb
        },
    },    

]

