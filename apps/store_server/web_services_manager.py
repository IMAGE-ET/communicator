
import xmlrpclib
from twisted.web import server, xmlrpc, http
from twisted.internet import defer

class WebServicesManager(xmlrpc.XMLRPC):

    def __init__(self, user='', password=''):
        xmlrpc.XMLRPC.__init__(self)
        self._user = user
        self._password = password
        self._auth = (self._user != '')

    def render(self, request):
        """ Overridden 'render' method which takes care of
        HTTP basic authorization """

        if self._auth:
            cleartext_token = self._user + ':' + self._password
            user = request.getUser()
            passwd = request.getPassword()

            if user == '' and passwd == '':
                request.setResponseCode(http.UNAUTHORIZED)
                return 'Authorization required!'
            else:
                token = user + ':' + passwd
                if token != cleartext_token:
                    request.setResponseCode(http.UNAUTHORIZED)
                    return 'Authorization Failed!'

        request.content.seek(0, 0)
        args, functionPath = xmlrpclib.loads(request.content.read())
        try:
            function = self._getFunction(functionPath)
        except xmlrpc.NoSuchFunction, f:
            self._cbRender(f, request)
        else:
            request.setHeader("content-type", "text/xml")
            defer.maybeDeferred(function, *args).addErrback(
                self._ebRender
                ).addCallback(
                self._cbRender, request
                )

        return server.NOT_DONE_YET

