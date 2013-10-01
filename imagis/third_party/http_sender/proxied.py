'''
Created on Oct 30, 2009

@author: sackufpi
'''

# del invento
import xmlrpclib
#import urlparse

# Sibling Imports
from twisted.web import resource, server, http
from twisted.internet import protocol, defer
from twisted.python import log, reflect, failure
from urlparse import urlparse



class QueryProtocol(http.HTTPClient):

    def connectionMade(self):
        self.sendCommand('POST', self.factory.path)
        self.sendHeader('User-Agent', 'Twisted/XMLRPClib')
        self.sendHeader('Host', self.factory.host)
        self.sendHeader('Content-type', 'text/xml')
        self.sendHeader('Content-length', str(len(self.factory.payload)))
        if self.factory.user:
            auth = '%s:%s' % (self.factory.user, self.factory.password)
            auth = auth.encode('base64').strip()
            self.sendHeader('Authorization', 'Basic %s' % (auth,))
        if self.factory.proxy_user:
            auth_proxy = '%s:%s' % (self.factory.proxy_user, self.factory.proxy_passwd)
            auth_proxy = auth_proxy.encode('base64').strip()
            self.sendHeader('Proxy-Authorization', 'Basic %s' % (auth_proxy,))    
        self.endHeaders()
        self.transport.write(self.factory.payload)

    def handleStatus(self, version, status, message):
        if status != '200':
            self.factory.badStatus(status, message)

    def handleResponse(self, contents):
        self.factory.parseResponse(contents)


payloadTemplate = """<?xml version="1.0"?>
<methodCall>
<methodName>%s</methodName>
%s
</methodCall>
"""


class _QueryFactory(protocol.ClientFactory):

    deferred = None
    protocol = QueryProtocol

    def __init__(self, path, host, method, user=None, password=None, \
                 proxy_user=None, proxy_passwd=None, allowNone=False, args=()):
        self.path, self.host = path, host
        self.user, self.password = user, password
        self.proxy_user = proxy_user
        self.proxy_passwd = proxy_passwd
        self.payload = payloadTemplate % (method,
            xmlrpclib.dumps(args, allow_none=allowNone))
        self.deferred = defer.Deferred()

    def parseResponse(self, contents):
        if not self.deferred:
            return
        try:
            response = xmlrpclib.loads(contents)[0][0]
        except:
            deferred, self.deferred = self.deferred, None
            deferred.errback(failure.Failure())
        else:
            deferred, self.deferred = self.deferred, None
            deferred.callback(response)

    def clientConnectionLost(self, _, reason):
        if self.deferred is not None:
            deferred, self.deferred = self.deferred, None
            deferred.errback(reason)

    clientConnectionFailed = clientConnectionLost

    def badStatus(self, status, message):
        deferred, self.deferred = self.deferred, None
        deferred.errback(ValueError(status, message))


class ProxiedXMLRPC:
    """
    A Proxy for making remote XML-RPC calls accross an HTTP proxy.

    Pass the URL of the remote XML-RPC server to the constructor,
    as well as the proxy host and port.

    Use proxy.callRemote('foobar', *args) to call remote method
    'foobar' with *args.
    """

    def __init__(self, reactor, url, proxy_host, proxy_port, user, password, \
                 http_proxy_user = None, http_proxy_passwd = None):
        self.reactor = reactor
        self.url = url
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        parts = urlparse(url)
        self.remote_host = parts[1]
        self.secure = parts[0] == 'https'
        self.user = user # no es el usuario en el proxy sino el del web server
        self.password = password
        self.http_proxy_user = http_proxy_user
        self.http_proxy_passwd = http_proxy_passwd
        
    def callRemote(self, method, *rargs):
        factory = _QueryFactory(self.url, self.remote_host, method, \
                     user = self.user, password = self.password, \
                     proxy_user = self.http_proxy_user, \
                     proxy_passwd = self.http_proxy_passwd, args = rargs)
        if self.secure:
            from twisted.internet import ssl
            self.reactor.connectSSL(self.proxy_host, self.proxy_port,
                               factory, ssl.ClientContextFactory())
        else:
            self.reactor.connectTCP(self.proxy_host, self.proxy_port, factory)
        return factory.deferred
