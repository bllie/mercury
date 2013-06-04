from base64 import b64decode
from logging import getLogger
from twisted.internet.protocol import Protocol

from drozer.server.files import FileProvider, ErrorResource
from drozer.server.receivers.http import HttpReceiver, HTTPResponse

class HTTP(HttpReceiver):
    """
    Basic implementation of an HTTP server.
    """
    
    __logger = getLogger(__name__)
    
    name = 'HTTP'
    
    def __init__(self, credentials, file_provider):
        self.__credentials = credentials
        self.__file_provider = file_provider
    
    def authenticated(self, authorization):
        """
        Checks the Authorization header, send to provide credentials
        to the server.
        """
        
        method, credentials = authorization.split(" ")
        username, password = b64decode(credentials).split(":")
        
        return method == "Basic" and username in self.__credentials and self.__credentials[username] == password
    
    def connectionMade(self):
        """
        Called when a connection is made to the HTTP Server. We write back a
        placeholder message, for testing.
        """
        
        HttpReceiver.connectionMade(self)
        
    def requestReceived(self, request):
        """
        Called when a complete HTTP request has been made to the HTTP server.
        """
        
        resource = None
        
        if request.verb == "DELETE":
            resource = self.__file_provider.get(request.resource)
            
            if resource != None and resource.reserved:
                resource = ErrorResource(request.resource, 403, "You are not authorized to delete the resource %s.")
            else:
                self.__file_provider.delete(request.resource)
                
                resource = ErrorResource(request.resource, 200, "Deleted: %s")
        elif request.verb == "GET":
            resource = self.__file_provider.get(request.resource)
        elif request.verb == "POST":
            if not "Authorization" in request.headers or not self.authenticated(request.headers["Authorization"]):
                resource = ErrorResource(request.resource, 401, "You must authenticate to write the resource %s.")
                
                response = resource.getResponse()
                response.headers["WWW-Authenticate"] = "Basic realm=\"drozer\""
                self.transport.write(str(response))
                self.transport.loseConnection()
                return
            else:
                resource = self.__file_provider.get(request.resource)
                
                if resource != None and resource.reserved:
                    resource = ErrorResource(request.resource, 403, "You are not authorized to write the resource %s.")
                else:
                    if "X-Drozer-Magic" in request.headers:
                        magic = request.headers["X-Drozer-Magic"]
                    else:
                        magic = None
                    
                    if self.__file_provider.create(request.resource, request.body, magic=magic):
                        resource = ErrorResource(request.resource, 201, "Location: %s")
                    else:
                        resource = ErrorResource(request.resource, 500, "The server encountered an error whilst creating the resource %s.")
        
        self.transport.write(str(resource.getResponse()))
        self.transport.loseConnection()
        