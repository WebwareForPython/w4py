import os
import time
import socket

from marshal import dumps

from MiscUtils.Configurable import Configurable


class Adapter(Configurable):

    def __init__(self, webKitDir):
        Configurable.__init__(self)
        self._webKitDir = webKitDir
        self._respData = []

    def name(self):
        return self.__class__.__name__

    def defaultConfig(self):
        return dict(
            NumRetries = 20,  # 20 retries when we cannot connect
            SecondsBetweenRetries = 3,  # 3 seconds pause between retries
            ResponseBufferSize = 8*1024,  # 8 kBytes
            Host = 'localhost',  # host running the app server
            AdapterPort = 8086)  # the default app server port

    def configFilename(self):
        return os.path.join(
            self._webKitDir, 'Configs', '%s.config' % self.name())

    def getChunksFromAppServer(self, env, myInput='',
            host=None, port=None):
        """Get response from the application server.

        Used by subclasses that are communicating with a separate app server
        via socket. Yields the unmarshaled response in chunks.
        """
        if host is None:
            host = self.setting('Host')
        if port is None:
            port = self.setting('AdapterPort')
        requestDict = dict(format='CGI', time=time.time(), environ=env)
        retries = 0
        while 1:
            try:
                # Send our request to the AppServer
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((host, port))
            except socket.error:
                # Retry
                if retries <= self.setting('NumRetries'):
                    retries += 1
                    time.sleep(self.setting('SecondsBetweenRetries'))
                else:
                    raise socket.error('timed out waiting for connection to app server')
            else:
                break
        data = dumps(requestDict)
        s.sendall(dumps(int(len(data))))
        s.sendall(data)
        s.sendall(myInput)
        s.shutdown(1)
        bufsize = self.setting('ResponseBufferSize')
        while 1:
            data = s.recv(bufsize)
            if not data:
                break
            yield data

    def transactWithAppServer(self, env, myInput='', host=None, port=None):
        """Get the full response from the application server."""
        self._respData[:] = []
        for data in self.getChunksFromAppServer(env, myInput, host, port):
            self.processResponse(data)
        return ''.join(self._respData)

    def processResponse(self, data):
        """Process response data as it arrives."""
        self._respData.append(data)
