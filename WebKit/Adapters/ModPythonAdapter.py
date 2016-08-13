#!/usr/bin/env python

"""WebWare for Python adapter for mod_python.

Contributed by: Dave Wallace
Modified by Jay Love and Geoff Talvola

Here's how I set up my Apache conf:

    <Location /WK >
       SetHandler python-program
       # add the directory that contains ModPythonAdapter.py
       PythonPath "sys.path+['/path/to/WebKit']"
       PythonOption AppWorkDir /path/to/dir/with/adapter.address
       PythonHandler WebKit.Adapters.ModPythonAdapter
       PythonDebug On
    </Location>

If you used the MakeAppWorkDir.py script to make a separate
application working directory, specify that path for the AppWorkDir
option, otherwise it should be in your WebKit directory in which case
you should use /path/to/WebKit/adapter.address

http://localhost/WK/Welcome

You may also send all requests with a .psp extension to WebKit
by adding these lines, outside of any location or directory:

    AddHandler python-program .psp
    PythonPath "sys.path+['/path/to/WebKit']"
    PythonHandler modpHandler::pspHandler
    PythonOption AppWorkDir /path/to/dir/with/adapter.address
"""

import os
import sys

from mod_python import apache

# Fix the current working directory -- this gets initialized incorrectly
# for some reason when run using mod_python
try:
    os.chdir(os.path.abspath(os.path.dirname(__file__)))
except Exception:
    pass

from Adapter import Adapter

debug = 0
__adapter = None
bufsize = 32 * 1024


class ModPythonAdapter(Adapter):

    def __init__(self, host, port, webKitDir):
        Adapter.__init__(self, webKitDir)
        self.host = host
        self.port = port

    def handler(self, req):
        self.reset(req)
        try:
            # Get input
            myInput = self.input(req)

            # get the apache module to do the grunt work of
            # building the environment
            env = apache.build_cgi_env(req)

            # make sure env is a dictionary (may not be for Apache2)
            env = dict(env)

            # Fix up the path
            if 'PATH_INFO' not in env:
                env['PATH_INFO'] = req.path_info

            # Communicate with the app server
            self.transactWithAppServer(env, myInput, self.host, self.port)
        except:
            self.handleException(req)
        return apache.OK

    def pspHandler(self, req):
        self.reset(req)
        try:
            # Get input
            myInput = self.input(req)

            # get the apache module to do the grunt work of
            #   building the environment
            env = apache.build_cgi_env(req)

            # make sure env is a dictionary (may not be for Apache2)
            env = dict(env)

            # Special environment setup needed for psp handler
            env['WK_ABSOLUTE'] = '1'

            # Fix up the path
            if 'PATH_INFO' not in env:
                env['PATH_INFO'] = req.path_info

            # Communicate with the app server
            self.transactWithAppServer(env, myInput, self.host, self.port)
        except Exception:
            self.handleException(req)
        return apache.OK

    def typehandler(self, req):
        """Type handler.

        Not being used yet. Probably never be used, because the req.handler
        field is read only in mod_python.
        """
        self.reset(req)
        debug = True
        if debug:
            ot = open('/tmp/log2.txt', 'a')
            ot.write("In type handler\n")
            ot.flush()

        if req.filename is None:
            return apache.DECLINED
        fn = req.filename
        ext = fn[fn.rfind('.'):]

        if debug:
            ot.write("TH: Filename: %s\n" % fn)
            ot.write("TH: Extension: %s\n" % ext)
            ot.write("Req_Handler = %s\n" % req.handler)
            ot.flush()
            ot.close()

        if ext == '.psp':
            req.handler = 'python-program'
            return apache.OK
        else:
            return apache.DECLINED

    def input(self, req):
        myInput = ''
        inp = req.read(bufsize)
        # this looks like bad performance if we don't get it all
        # in the first buffer
        while inp:
            myInput += inp
            inp = req.read(bufsize)
        return myInput

    def processResponse(self, data):
        req = self.request()
        if self.doneHeader():
            req.write(data)
            return
        headerData = self.headerData() + data
        self.setHeaderData(headerData)
        headerEnd = headerData.find('\r\n\r\n')
        if headerEnd < 0:
            return
        headers = headerData[:headerEnd]
        for header in headers.split('\r\n'):
            colon = header.find(':')
            name = header[:colon]
            value = header[colon+1:]
            req.headers_out.add(name, value)
            if name.lower() == 'content-type':
                req.content_type = value
            if name.lower() == 'status':
                req.status = int(value.lstrip().split(None, 1)[0])
        req.send_http_header()
        req.write(headerData[headerEnd+4:])
        self.setDoneHeader(1)

    def handleException(self, req):
        import traceback

        apache.log_error('WebKit mod_python: Error while responding to request\n')
        apache.log_error('Python exception:\n')
        traceback.print_exc(file=sys.stderr)

        output = traceback.format_exception(*sys.exc_info())
        output = ''.join(output)
        output = output.replace('&', '&amp;'
            ).replace('<', '&lt;').replace('>', '&gt;')
        req.write('''
<html><body>
<p><pre>ERROR

%s</pre>
</body></html>\n''' % output)

    def reset(self, request):
        self.setDoneHeader(0)
        self.setHeaderData('')
        self.setRequest(request)

    # These methods are non-thread-safe. On platforms like NT where Apache
    # runs multi-threaded, and the same ModPythonAdapter instance may be
    # called simultaneously for different requests, they need to replaced
    # with thread-safe versions. See WinModPythonAdapter below.

    def doneHeader(self):
        return self._doneHeader

    def setDoneHeader(self, doneHeader):
        self._doneHeader = doneHeader

    def headerData(self):
        return self._headerData

    def setHeaderData(self, headerData):
        self._headerData = headerData

    def request(self):
        return self._request

    def setRequest(self, request):
        self._request = request


# NT-specific, thread-safe version of ModPythonAdapter. Requires Win32 extensions.

if os.name == 'nt':
    import win32api

    # This is a Windows-specific thread-safe version of ModPythonAdapter.
    # It replaces the non-thread-safe [set]doneHeader, [set]headerData, and
    # [set]request with versions that store the information keyed by thread ID.
    #
    # This seems a bit hokey, but it was easy to write and it works.

    OriginalModPythonAdapter = ModPythonAdapter

    class WinModPythonAdapter(OriginalModPythonAdapter):

        def __init__(self, host, port, webKitDir):
            OriginalModPythonAdapter.__init__(self, host, port, webKitDir)
            self._threadSafeStorage = {}

        def threadSafeValue(self, name):
            threadID = win32api.GetCurrentThreadId()
            return self._threadSafeStorage[threadID, name]

        def setThreadSafeValue(self, name, value):
            threadID = win32api.GetCurrentThreadId()
            self._threadSafeStorage[threadID, name] = value

        def doneHeader(self):
            return self.threadSafeValue('doneHeader')

        def setDoneHeader(self, doneHeader):
            self.setThreadSafeValue('doneHeader', doneHeader)

        def headerData(self):
            return self.threadSafeValue('headerData')

        def setHeaderData(self, headerData):
            self.setThreadSafeValue('headerData', headerData)

        def request(self):
            return self.threadSafeValue('request')

        def setRequest(self, request):
            self.setThreadSafeValue('request', request)

    # Replace ModPythonAdapter with the Windows-safe version.
    ModPythonAdapter = WinModPythonAdapter


def _adapter(req):
    global __adapter
    if __adapter is None:
        appWorkDir = req.get_options()['AppWorkDir']
        WEBWARE_ADDRESS_FILE = os.path.join(appWorkDir, 'adapter.address')
        host, port = open(WEBWARE_ADDRESS_FILE).read().split(':')
        port = int(port)
        __adapter = ModPythonAdapter(host, port, appWorkDir)
    return __adapter


def handler(req):
    return _adapter(req).handler(req)


def pspHandler(req):
    return _adapter(req).pspHandler(req)


def typehandler(req):
    return _adapter(req).typehandler(req)
