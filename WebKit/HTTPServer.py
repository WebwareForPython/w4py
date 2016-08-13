"""HTTP servlets"""

import os
import socket
import errno
import BaseHTTPServer

from ThreadedAppServer import Handler
from ASStreamOut import ASStreamOut


class HTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """Handles incoming requests.

    Recreated with every request. Abstract base class.
    """

    # This sends the common CGI variables, except the following:
    # HTTP_CONNECTION, HTTP_KEEP_ALIVE
    # DOCUMENT_ROOT, PATH_TRANSLATED, SCRIPT_FILENAME
    # SERVER_NAME, SERVER_ADMIN, SERVER_SIGNATURE

    def handleRequest(self):
        """Handle a request.

        Actually performs the request, creating the environment and calling
        self.doTransaction(env, input) to perform the response.
        """
        self.server_version = 'Webware/' + self._server.version()
        env = {}
        for header in ('Content-Type', 'Content-Length', 'If-Modified-Since'):
            # unfortunately, self.headers has no pop() method
            if header in self.headers:
                env[header.upper().replace('-', '_')] = self.headers[header]
                del self.headers[header]
        self.headersToEnviron(self.headers, env)
        env['REMOTE_ADDR'], env['REMOTE_PORT'] = map(str, self.client_address)
        env['REQUEST_METHOD'] = self.command
        path = self.path
        if '?' in path:
            env['REQUEST_URI'], env['QUERY_STRING'] = path.split('?', 1)
        else:
            env['REQUEST_URI'] = path
            env['QUERY_STRING'] = ''
            env['SCRIPT_NAME'] = ''
        env['PATH'] = os.getenv('PATH', '')
        env['PATH_INFO'] = env['REQUEST_URI']
        env['SERVER_ADDR'], env['SERVER_PORT'] = map(str, self._serverAddress)
        env['SERVER_SOFTWARE'] = self.server_version
        env['SERVER_PROTOCOL'] = self.protocol_version
        env['GATEWAY_INTERFACE'] = 'CGI/1.1'
        self.doTransaction(env, self.rfile)

    do_GET = do_POST = do_HEAD = handleRequest
    # These methods are used in WebDAV requests:
    do_OPTIONS = do_PUT = do_DELETE = handleRequest
    do_MKCOL = do_COPY = do_MOVE = handleRequest
    do_PROPFIND = handleRequest

    @staticmethod
    def headersToEnviron(headers, env):
        """Convert headers to environment variables.

        Use a simple heuristic to convert all the headers to
        environmental variables.
        """
        for header, value in headers.items():
            env['HTTP_%s' % header.upper().replace('-', '_')] = value
        return env

    def processResponse(self, data):
        """Process response.

        Takes a string (like what a CGI script would print) and
        sends the actual HTTP response (response code, headers, body).
        """
        status, data = data.split('\r\n', 1)
        status, code, message = status.split(None, 2)
        try:
            assert status == 'Status:'
            code = int(code)
            assert 2 <= code/100 < 6
        except Exception:
            print '%5d  HTTPServer error: Missing status header' % (
                self._requestID,)
        else:
            self.send_response(code, message)
            self.wfile.write(data)

    def log_request(self, code='-', size='-'):
        """Log an accepted request.

        Do nothing (use the LogActivity setting instead).
        """
        pass


class HTTPAppServerHandler(Handler, HTTPHandler):
    """AppServer interface.

    Adapters HTTPHandler to fit with ThreadedAppServer's model of an adapter.
    """
    protocolName = 'http'
    settingPrefix = 'HTTP'

    def handleRequest(self):
        """Handle a request."""
        HTTPHandler.__init__(self, self._sock, self._sock.getpeername(), None)

    def doTransaction(self, env, input):
        """Process transaction."""
        requestDict = dict(format='CGI', environ=env, input=input)
        self.startRequest(requestDict)
        streamOut = ASStreamOut()
        self.dispatchRawRequest(requestDict, streamOut)
        try:
            self.processResponse(streamOut._buffer)
            self._sock.shutdown(2)
        except socket.error as e:
            if e[0] == errno.EPIPE:  # broken pipe
                return
            print '%5d  HTTPServer output error: %s' % (
                self._requestID, e)
        self.endRequest()

    def dispatchRawRequest(self, requestDict, streamOut):
        """Dispatch the request."""
        transaction = self._server._app.dispatchRawRequest(requestDict, streamOut)
        streamOut.close()
        transaction._application = None
        transaction.die()
        del transaction
