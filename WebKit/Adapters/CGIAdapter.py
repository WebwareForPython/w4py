#!/usr/bin/env python

"""CGIAdapter.py

This is the CGI Adapter for the WebKit AppServer.

This CGI script collects information about the request, puts it into a
package, and then sends it to the WebKit application server over TCP/IP.

This script expects to find a file in its directory called
'adapter.address' that specifies the address of the app server.
The file is written by the app server upon successful startup
and contains nothing but:

hostname:port

with no other characters, not even a newline. For example,

localhost:8086

or even:

:8086

...since an empty string is a special case indicating the local host.
"""

import sys
import os
import time

from Adapter import Adapter


class CGIAdapter(Adapter):

    def run(self):

        response = None
        try:
            # MS Windows: no special translation of end-of-lines
            if os.name == 'nt':
                import msvcrt
                msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
                msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)

            myInput = ''
            if 'CONTENT_LENGTH' in os.environ:
                length = int(os.environ['CONTENT_LENGTH'])
                myInput += sys.stdin.read(length)

            # 2000-05-20 ce: For use in collecting raw request dictionaries for use in Tests/stress.py
            # Leave this code here in case it's needed again:
            # counter = int(open('counter.text').read())
            # counter += 1
            # open('counter.text', 'w').write(str(counter))
            # open('rr-%02d.rr' % counter, 'w').write(str(dict))

            host, port = open(os.path.join(self._webKitDir,
                'adapter.address')).read().split(':', 1)
            if os.name == 'nt' and not host:
                host = 'localhost'  # MS Windows doesn't like a blank host name
            port = int(port)

            response = self.transactWithAppServer(os.environ.data, myInput, host, port)

        except:
            import traceback
            sys.stderr.write('[%s] [error] WebKit.CGIAdapter:'
                ' Error while responding to request (unknown)\n'
                % (time.asctime(time.localtime(time.time()))))
            sys.stderr.write('Python exception:\n')
            traceback.print_exc(file=sys.stderr)
            output = ''.join(traceback.format_exception(*sys.exc_info()))
            output = "<pre>%s</pre>" % htmlEncode(output)
            if response is None:
                output = "<h4>No response from application server</h4>\n" + output
            sys.stdout.write('''Content-Type: text/html\n
<html><head><title>WebKit CGI Error</title><body>
<h3>WebKit CGI Error</h3>
%s
</body></html>\n''' % output)

    def processResponse(self, data):
        sys.stdout.write(data)
        sys.stdout.flush()


htmlCodes = (
    ('&', '&amp;'),
    ('<', '&lt;'),
    ('>', '&gt;'),
    ('"', '&quot;'),
)


def htmlEncode(s, codes=htmlCodes):
    """Returns the HTML encoded version of the given string.

    This is useful to display a plain ASCII text string on a web page.
    (We could get this from WebUtils, but we're keeping CGIAdapter
    independent of everything but standard Python.)
    """
    for c, e in codes:
        s = s.replace(c, e)
    return s


def main(webKitDir):
    CGIAdapter(webKitDir).run()
