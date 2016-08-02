"""OneShotAdapter.py

This is a special version of the CGIAdapter that doesn't require a persistent
AppServer process. This is mostly useful during development when repeated
changes to classes forces the developer to restart the app server to make
the changes take effect.

An example, URL:

    http://127.0.0.1/OneShot.cgi/MyPage
"""

import sys
import os
import time
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from WebKit.Adapters.Adapter import Adapter
from MiscUtils.Funcs import charWrap
from WebUtils.Funcs import htmlEncode


class OneShotAdapter(Adapter):

    def defaultConfig(self):
        config = Adapter.defaultConfig(self)
        config.update(
            ShowConsole = False,
            ConsoleWidth = 80,  # use 0 to turn off
            ConsoleHangingIndent = 4,
        )
        return config

    def run(self):

        timestamp = time.time()  # start time

        # to capture the console output of the application
        stdout, sys.stdout = sys.stdout, StringIO()

        try:

            # MS Windows: no special translation of end-of-lines
            if os.name == 'nt':
                import msvcrt
                msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)

            requestDict = dict(
                format='CGI', time=timestamp,
                # ce: a little tricky. We use marshal which only works
                # on built-in types, so we need environ's dictionary:
                environ=os.environ.data, input=sys.stdin)

            from WebKit import Profiler
            Profiler.startTime = time.time()

            print 'ONE SHOT MODE\n'

            from WebKit.OneShotAppServer import OneShotAppServer
            appSvr = OneShotAppServer(self._webKitDir)

            # It is important to call transaction.die() after using it, rather than
            # just letting it fall out of scope, to avoid circular references
            from WebKit.ASStreamOut import ASStreamOut
            rs = ASStreamOut()
            transaction = appSvr.dispatchRawRequest(requestDict, rs)
            rs.close()
            if transaction:
                transaction.die()
                del transaction

            appSvr.shutDown()
            appSvr = None

            print "AppServer run time %.2f seconds" % (time.time() - Profiler.startTime)

            sys.stdout = stdout

            # MS Windows: no special translation of end-of-lines
            if os.name == 'nt':
                import msvcrt
                msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

            response = rs._buffer
            if response:
                sys.stdout.write(response)
            else:
                sys.stdout.write('''Content-Type: text/html\n
<html><head><title>WebKit CGI Error</title><body>
<h3>WebKit CGI Error</h3>
<h4>No response from application server</h4>
</body></html>\n''')

            if self.setting('ShowConsole'):
                # show the contents of the console,
                # but only if we are serving up an HTML file
                endheaders = response.find("\r\n\r\n")
                if endheaders < 0:
                    endheaders = response.find("\n\n")
                if not endheaders:
                    print "No Headers Found"
                    return
                headers = response[:endheaders].split("\n")
                entries = []
                for header in headers:
                    if header:
                        entries.append(header.split(":", 1))
                found = False
                for name, value in entries:
                    if name.lower() == 'content-type':
                        found = True
                        break
                if found and value.strip().lower() == 'text/html':
                    self.showConsole(_console.getvalue())
        except:
            import traceback
            sys.stderr.write('[%s] [error] WebKit.OneShotAdapter:'
                ' Error while responding to request (unknown)\n'
                % (time.asctime(time.localtime(time.time()))))
            sys.stderr.write('Python exception:\n')
            traceback.print_exc(file=sys.stderr)
            sys.stdout = stdout
            output = ''.join(traceback.format_exception(*sys.exc_info()))
            output = htmlEncode(output)
            sys.stdout.write('''Content-Type: text/html\n
<html><head><title>WebKit CGI Error</title><body>
<h3>WebKit CGI Error</h3>
<pre>%s</pre>
</body></html>\n''' % output)

    def showConsole(self, contents):
        width = self.setting('ConsoleWidth')
        if width:
            contents = charWrap(contents, self.setting('ConsoleWidth'),
                self.setting('ConsoleHangingIndent'))
        contents = htmlEncode(contents)
        sys.stdout.write('''<br><br><table>
<tr><td style="background-color: #eee">
<pre>%s</pre>
</td></tr></table>''' % contents)


def main(webKitDir=None):
    if webKitDir is None:
        webKitDir = os.path.dirname(os.getcwd())
    try:
        OneShotAdapter(webKitDir).run()
    except:
        import traceback
        sys.stderr.write('[%s] [error] OneShotAdapter:'
            ' Error while responding to request (unknown)\n'
            % (time.asctime(time.localtime(time.time()))))
        sys.stderr.write('Python exception:\n')
        traceback.print_exc(file=sys.stderr)
        output = ''.join(traceback.format_exception(*sys.exc_info()))
        output = htmlEncode(output)
        sys.stdout.write('''Content-Type: text/html\n
<html><head><title>CGI Error</title><body>
<h3>CGI Error</h3>
<pre>%s</pre>
</body></html>\n''' % output)
