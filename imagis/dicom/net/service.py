# python imports
from string import Template

# imagis imports
from imagis.utils.process import Popen




class ExternalService(object):

    def __init__(self, template):
        self._template = Template(template)
        self._command = None
        #self.
        self._process = None

    def start(self):
        pass

    def stop(self):
        pass


