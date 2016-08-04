#!/usr/bin/env python

"""FCGIAdapter.py

FCGI Adapter for the WebKit application environment.

Note: FCGI for Webware is not available on Windows.

This script is started by the Web Server and is kept running.
When a request comes through here, this script collects information
about the request, puts it into a package, and then invokes the
WebKit Application to handle it.

Original CGI implementation by Chuck Esterbrook.

FastCGI Implementation by Jay Love.
Based on threaded fcgi example "sz_fcgi" provided by Andreas Jung.


SETUP

To use this adapter, you must have a fastcgi capable web server.

For Apache, you'll need to add the following lines to your httpd.conf file, or
put them in another file and include that file in httpd.conf

# I have the file in my cgi-bin directory, but you might as well put it in html.
# the -host is the port it communicates on
# the path is from the SERVER ROOT

    FastCgiExternalServer ../fcgi-bin/FCGIAdapter.py -host localhost:33333

    <Directory ../fcgi-bin>
        SetHandler fastcgi-script
        Options ExecCGI FollowSymLinks
    </Directory>

You could also take an extension oriented approach in Apache using '.fcgi':

    AddHandler fastcgi-script fcgi

And then using, in your URLs, 'WebKit.fcgi' which is a link to this file. e.g.,:

    http://localhost/Webware/WebKit/WebKit.fcgi/Introspect


FUTURE

(*) There are some interesting lines at the top of fcgi.py:

# Set various FastCGI constants
# Maximum number of requests that can be handled
FCGI_MAX_REQS = 1
FCGI_MAX_CONNS = 1

# Boolean: can this application multiplex connections?
FCGI_MPXS_CONNS = 0

Do these need to be adjusted in order to realize the full benefits of FastCGI?

(*) Has anyone measured the performance difference between CGIAdapter and FCGIAdapter? What are the results?

JSL- It's twice as fast as straight CGI


CHANGES

* 2000-05-08 ce:
  * Fixed bug in exception handler to send first message to stderr, instead of stdout
  * Uncommented the line for reading 'adapter.address'
  * Switched from eval() encoding to marshal.dumps() encoding in accordance with AppServer
  * Increased rec buffer size from 8KB to 32KB
  * Removed use of pr() for feeding app server results back to webserver. Figure that's slightly more efficient.
  * Added notes about how I set this up with Apache to what was already there.

*2001-03-14 jsl:
  * Fixed problem with post data
"""

# If you used the MakeAppWorkDir.py script to make a separate
# application working directory, specify it here:
workDir = None

# If the Webware installation is located somewhere else,
# then set the webwareDir variable to point to it here:
webwareDir = None

import sys
import os
import time

if not webwareDir:
    webwareDir = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.realpath(__file__))))
sys.path.insert(1, webwareDir)
webKitDir = os.path.join(webwareDir, 'WebKit')
sys.path.insert(1, webKitDir)
if not workDir:
    workDir = webKitDir

from WebKit.Adapters import fcgi
from WebKit.Adapters.Adapter import Adapter


class FCGIAdapter(Adapter):

    def run(self):
        """Block waiting for new request."""
        while fcgi.isFCGI():
            req = fcgi.FCGI()
            self.FCGICallback(req)

    def FCGICallback(self, req):
        """This function is called whenever a request comes in."""
        try:
            # Transact with the app server
            myInput = req.inp.read()
            response = self.transactWithAppServer(
                req.env, myInput, host, port)
            # deliver it!
            req.out.write(response)
            req.out.write(repr(len(myInput)))
            req.out.flush()
        except Exception:
            import traceback
            # Log the problem to stderr
            stderr = req.err
            stderr.write('[%s] [error] WebKit.FCGIAdapter:'
                ' Error while responding to request (unknown)\n'
                % (time.asctime(time.localtime(time.time()))))
            stderr.write('Python exception:\n')
            traceback.print_exc(file=stderr)
            # Report the problem to the browser
            output = ''.join(traceback.format_exception(*sys.exc_info()))
            output = htmlEncode(output)
            sys.pr('''Content-Type: text/html\n
<html><head><title>WebKit CGI Error</title><body>
<h3>WebKit CGI Error</h3>
%s
</body></html>\n''' % output)
        req.Finish()
        return

    def pr(self, *args):
        """Just a quick and easy print function."""
        try:
            req = self.req
            req.out.write(''.join(map(str, args)) + '\n')
            req.out.flush()
        except Exception:
            pass


htmlCodes = (
    ('&', '&amp;'),
    ('<', '&lt;'),
    ('>', '&gt;'),
    ('"', '&quot;'),
)

def htmlEncode(s, codes=htmlCodes):
    """Return the HTML encoded version of the given string.

    This is useful to display a plain ASCII text string on a web page.
    (We could get this from WebUtils, but we're keeping FCGIAdapter
    independent of everything but standard Python.)
    """
    for c, e in codes:
        s = s.replace(c, e)
    return s


# Start FCGI Adapter

if os.name != 'posix':
    print "This adapter is only available on UNIX"
    sys.exit(1)

fcgi._startup()
if not fcgi.isFCGI():
    print "No FCGI Environment Available"
    print "This module cannot be run from the command line"
    sys.exit(1)

address = open(os.path.join(workDir, 'adapter.address')).read()
host, port = address.split(':', 1)
port = int(port)

fcgiloop = FCGIAdapter(workDir)
fcgiloop.run()
