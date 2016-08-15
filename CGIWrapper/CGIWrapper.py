#!/usr/bin/env python

"""CGIWrapper.py

Webware for Python

See the CGIWrapper.html documentation for more information.
"""

# We first record the starting time, in case we're being run as a CGI script.
from time import time, localtime, asctime
serverStartTime = time()

# Some imports
import cgi
import os
import sys
import traceback
from random import randint
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

if '' not in sys.path:
    sys.path.insert(0, '')

from Properties import version

try:
    import WebUtils
except ImportError:
    sys.path.append(os.path.abspath('..'))
    import WebUtils

from WebUtils.HTMLForException import HTMLForException

from MiscUtils.NamedValueAccess import valueForName


class CGIWrapper(object):
    """The CGI Wrapper class.

    A CGI wrapper executes a target script and provides various services
    for both the script and website developer and the administrator.

    See the CGIWrapper.html documentation for full information.
    """


    ## Init ##

    def __init__(self):
        self._config = self.config()


    ## Configuration ##

    def defaultConfig(self):
        """Return a dictionary with the default configuration.

        Subclasses could override to customize the values
        or where they're taken from.
        """
        return dict(
            ScriptsHomeDir = 'Examples',
            ChangeDir = True,
            ExtraPaths = [],
            ExtraPathsIndex = 1,
            LogScripts = True,
            ScriptLogFilename = 'Scripts.csv',
            ScriptLogColumns = [
                'environ.REMOTE_ADDR',
                'environ.REQUEST_METHOD', 'environ.REQUEST_URI',
                'responseSize', 'scriptName',
                'serverStartTimeStamp', 'serverDuration',
                'scriptDuration', 'errorOccurred'
            ],
            ClassNames = ['', 'Page'],
            ShowDebugInfoOnErrors = True,
            UserErrorMessage = 'The site is having technical difficulties'
                ' with this page. An error has been logged, and the problem'
                ' will be fixed as soon as possible. Sorry!',
            LogErrors = True,
            ErrorLogFilename = 'Errors.csv',
            SaveErrorMessages = True,
            ErrorMessagesDir = 'ErrorMsgs',
            EmailErrors = False,
            ErrorEmailServer = 'localhost',
            ErrorEmailHeaders = {
                'From': 'webware@mydomain',
                'To': ['webware@mydomain'],
                'Reply-To': 'webware@mydomain',
                'Content-Type': 'text/html',
                'Subject': 'Error'
            },
            AdminRemoteAddr = ['127.0.0.1']
        )

    def configFilename(self):
        """Return the filename of the optional configuration file."""
        return 'CGIWrapper.config'

    def userConfig(self):
        """Return a dictionary with the user configuration.

        This are overrides found in the optional configuration file,
        or {} if there is no such file. The config filename is taken
        from configFilename().
        """
        try:
            f = open(self.configFilename())
        except IOError:
            return {}
        else:
            config = f.read()
            config = eval('dict(%s)' % config)
            f.close()
            assert isinstance(config, dict)
            return config

    def config(self):
        """Return the configuration for the CGIWrapper.

        This is a combination of defaultConfig() and userConfig().
        This method does no caching.
        """
        config = self.defaultConfig()
        config.update(self.userConfig())
        return config

    def setting(self, name):
        """Return the value of a particular setting in the configuration."""
        return self._config[name]


    ## Utilities ##

    def docType(self):
        return docType()

    def makeHeaders(self):
        """Return a default header dictionary with Content-Type entry."""
        return {'Content-Type': 'text/html'}

    def makeFieldStorage(self):
        """Return a default field storage object created from the cgi module."""
        return cgi.FieldStorage()

    def enhanceThePath(self):
        """Enhance sys.path according to our configuration."""
        extraPathsIndex = self.setting('ExtraPathsIndex')
        sys.path[extraPathsIndex:extraPathsIndex] = self.setting('ExtraPaths')

    def environ(self):
        """Get the environment for the request."""
        return self._environ

    def requireEnvs(self, names):
        """Check that given environment variable names exist.

        If they don't, a basic HTML error message is printed and we exit.
        """
        badNames = [name for name in names if name not in self._environ]
        if badNames:
            print 'Content-Type: text/html'
            print
            print docType()
            print '<html><head><title>Error</title></head><body>'
            print '<p>ERROR: Missing %s</p>' % ', '.join(badNames)
            print '</body></html>'
            sys.exit(0)

    def scriptPathname(self):
        """Return the full pathname of the target script.

        Scripts that start with an underscore are special -- they run
        out of the same directory as the CGI Wrapper and are typically
        CGI Wrapper support scripts.
        """
        # remove the CGI Wrapper's filename part
        pathname = os.path.split(self._environ['SCRIPT_FILENAME'])[0]
        filename = self._environ['PATH_INFO'][1:]
        ext = os.path.splitext(filename)[1]
        if ext:
            # Hmmm, some kind of extension like maybe '.html'.
            # Leave out the 'ScriptsHomeDir' and leave the extension alone.
            filename = os.path.join(pathname, filename)
            self._servingScript = False
        else:
            # No extension - we assume a Python CGI script.
            if filename.startswith('_'):
                # Underscores denote private scripts packaged with CGI Wrapper,
                # such as '_admin.py'.
                if self.setting('AdminRemoteAddr'):
                    # Users with the wrong remote address are redirected
                    # to the access denied script.
                    self.requireEnvs(['REMOTE_ADDR'])
                    remoteAddr = self._environ['REMOTE_ADDR'] + '.'
                    for addr in self.setting('AdminRemoteAddr'):
                        if remoteAddr.startswith(addr + '.'):
                            break
                    else:
                        filename = '_accessDenied'
                filename = os.path.join(pathname, filename + '.py')
            else:
                # All other scripts are based in the directory named
                # by the 'ScriptsHomeDir' setting.
                filename = os.path.join(pathname,
                    self.setting('ScriptsHomeDir'), filename + '.py')
            self._servingScript = True
        return filename

    def writeScriptLog(self):
        """Write an entry to the script log file.

        Uses settings ScriptLogFilename and ScriptLogColumns.
        """
        filename = self.setting('ScriptLogFilename')
        if os.path.exists(filename):
            f = open(filename, 'a')
        else:
            f = open(filename, 'w')
            f.write(','.join(self.setting('ScriptLogColumns')) + '\n')
        values = []
        for column in self.setting('ScriptLogColumns'):
            value = valueForName(self, column)
            if isinstance(value, float):
                # might need more flexibility in the future
                value = '%0.4f' % value
            else:
                value = str(value)
            values.append(value)
        f.write(','.join(values) + '\n')
        f.close()

    def version(self):
        return '.'.join(map(str, version))


    ## Exception handling ##

    def handleException(self, excInfo):
        """Handle an exception in the target script.

        Invoked by self when an exception occurs in the target script.
        <code>excInfo</code> is a sys.exc_info()-style tuple of information
        about the exception.
        """
        # Note the duration of the script and time of the exception
        self._scriptEndTime = time()
        self.logExceptionToConsole()
        self.reset()
        print self.htmlErrorPage(
            showDebugInfo=self.setting('ShowDebugInfoOnErrors'))
        fullErrorMsg = None
        if self.setting('SaveErrorMessages'):
            fullErrorMsg = self.htmlErrorPage(showDebugInfo=True)
            filename = self.saveHTMLErrorPage(fullErrorMsg)
        else:
            filename = ''
        self.logExceptionToDisk(filename)
        if self.setting('EmailErrors'):
            if fullErrorMsg is None:
                fullErrorMsg = self.htmlErrorPage(showDebugInfo=True)
            self.emailException(fullErrorMsg)

    def logExceptionToConsole(self, stderr=sys.stderr):
        """Log an exception in the target script.

        Logs the time, script name and traceback to the console
        (typically stderr). This usually results in the information
        appearing in the web server's error log. Used by handleException().
        """
        # stderr logging
        stderr.write('[%s] [error] CGI Wrapper:'
            ' Error while executing script %s\n' % (
            asctime(localtime(self._scriptEndTime)), self._scriptPathname))
        traceback.print_exc(file=stderr)

    def reset(self):
        """Reset CGI output.

        Used by handleException() to clear out the current CGI output results
        in preparation of delivering an HTML error message page.
        Currently resets headers and deletes cookies, if present.
        """
        # Set headers to basic text/html. We don't want stray headers
        # from a script that failed.
        self._headers = self.makeHeaders()
        # Get rid of cookies, too
        if 'cookies' in self._namespace:
            del self._namespace['cookies']

    def htmlErrorPage(self, showDebugInfo=True):
        """Return an HTML page explaining that there is an error.

        There could be more options in the future, so using named arguments
        (e.g. showDebugInfo=False) is recommended. Invoked by handleException().
        """
        html = ['''%s
<html>
<title>Error</title>
<body style="color:black;background-color:white">
%s<p>%s</p>
''' % (docType(), htTitle('Error'), self.setting('UserErrorMessage'))]

        if self.setting('ShowDebugInfoOnErrors'):
            html.append(self.htmlDebugInfo())

        html.append('</body></html>')
        return ''.join(html)

    def htmlDebugInfo(self):
        """Return an HTML page with debugging info on the current exception.

        Used by handleException().
        """
        html = ['''
%s<p><i>%s</i></p>
''' % (htTitle('Traceback'), self._scriptPathname)]
        html.append(HTMLForException())
        html.extend([
            htTitle('Misc Info'),
            htDictionary({
                'time': asctime(localtime(self._scriptEndTime)),
                'filename': self._scriptPathname,
                'os.getcwd()': os.getcwd(),
                'sys.path': sys.path
            }),
            htTitle('Fields'), htDictionary(self._fields),
            htTitle('Headers'), htDictionary(self._headers),
            htTitle('Environment'), htDictionary(self._environ, {'PATH': ';'}),
            htTitle('Ids'), htTable(osIdTable(), ['name', 'value'])])
        return ''.join(html)

    def saveHTMLErrorPage(self, html):
        """Save the given HTML error page for later viewing by the developer.

        Returns the filename used. Invoked by handleException().
        """
        dir = self.setting('ErrorMessagesDir')
        if not os.path.exists(dir):
            os.makedirs(dir)
        filename = os.path.join(dir, self.htmlErrorPageFilename())
        try:
            with open(filename, 'w') as f:
                f.write(html)
        except IOError:
            sys.stderr.write('[%s] [error] CGI Wrapper: Cannot save error page (%s)\n'
                % (asctime(localtime(time())), filename))
        else:
            return filename

    def htmlErrorPageFilename(self):
        """Construct a filename for an HTML error page.

        This filename does not include the 'ErrorMessagesDir' setting.
        """
        # Note: Using the timestamp and a random number is a poor technique
        # for filename uniqueness, but it is fast and good enough in practice.
        return 'Error-%s-%s-%06d.html' % (os.path.split(self._scriptPathname)[1],
            '-'.join(map(lambda x: '%02d' % x, localtime(self._scriptEndTime)[:6])),
            randint(0, 999999))

    def logExceptionToDisk(self, errorMsgFilename=None, excInfo=None):
        """Write exception info to the log file.

        Writes a tuple containing (date-time, filename, pathname,
        exception-name, exception-data, error report filename)
        to the errors file (typically 'Errors.csv') in CSV format.
        Invoked by handleException().
        """
        if not excInfo:
            excInfo = sys.exc_info()
        err, msg = excInfo[:2]
        err, msg = err.__name__, str(msg)
        logline = (asctime(localtime(self._scriptEndTime)),
            os.path.split(self._scriptPathname)[1], self._scriptPathname,
            err, msg, errorMsgFilename or '')
        def fixElement(element):
            element = str(element)
            if ',' in element or '"' in element:
                element = element.replace('"', '""')
                element = '"%s"' % element
            return element
        logline = map(fixElement, logline)
        filename = self.setting('ErrorLogFilename')
        if os.path.exists(filename):
            f = open(filename, 'a')
        else:
            f = open(filename, 'w')
            f.write('time,filename,pathname,exception name,'
                'exception data,error report filename\n')
        f.write(','.join(logline) + '\n')
        f.close()

    def emailException(self, html, excInfo=None):
        """Email an exception."""
        # Construct the message
        if not excInfo:
            excInfo = sys.exc_info()
        headers = self.setting('ErrorEmailHeaders')
        msg = []
        for key in headers:
            if key != 'From' and key != 'To':
                msg.append('%s: %s\n' % (key, headers[key]))
        msg.append('\n')
        msg.append(html)
        msg = ''.join(msg)
        # Send the message
        import smtplib
        server = smtplib.SMTP(self.setting('ErrorEmailServer'))
        server.set_debuglevel(0)
        server.sendmail(headers['From'], headers['To'], msg)
        server.quit()


    ## Serve ##

    def serve(self, environ=os.environ):
        """Serve a request."""
        # Record the time
        if 'isMain' in globals():
            self._serverStartTime = serverStartTime
        else:
            self._serverStartTime = time()
        self._serverStartTimeStamp = asctime(localtime(self._serverStartTime))

        # Set up environment
        self._environ = environ

        # Ensure that filenames and paths have been provided
        self.requireEnvs(['SCRIPT_FILENAME', 'PATH_INFO'])

        # Set up the namespace
        self._headers = self.makeHeaders()
        self._fields = self.makeFieldStorage()
        self._scriptPathname = self.scriptPathname()
        self._scriptName = os.path.split(self._scriptPathname)[1]

        self._namespace = dict(
            headers=self._headers, fields=self._fields,
            environ=self._environ, wrapper=self)
        info = self._namespace.copy()

        # Set up sys.stdout to be captured as a string. This allows scripts
        # to set CGI headers at any time, which we then print prior to
        # printing the main output. This also allows us to skip on writing
        # any of the script's output if there was an error.
        #
        # This technique was taken from Andrew M. Kuchling's Feb 1998
        # WebTechniques article.
        #
        self._realStdout = sys.stdout
        sys.stdout = StringIO()

        # Change directories if needed
        if self.setting('ChangeDir'):
            origDir = os.getcwd()
            os.chdir(os.path.split(self._scriptPathname)[0])
        else:
            origDir = None

        # A little more setup
        self._errorOccurred = False
        self._scriptStartTime = time()

        # Run the target script
        try:
            if self._servingScript:
                execfile(self._scriptPathname, self._namespace)
                for name in self.setting('ClassNames'):
                    if not name:
                        name = os.path.splitext(self._scriptName)[0]
                    if name in self._namespace:
                        # our hook for class-oriented scripts
                        print self._namespace[name](info).html()
                        break
            else:
                self._headers = {'Location':
                    os.path.split(self._environ['SCRIPT_NAME'])[0]
                    + self._environ['PATH_INFO']}

            # Note the end time of the script
            self._scriptEndTime = time()
            self._scriptDuration = self._scriptEndTime - self._scriptStartTime
        except:
            # Note the end time of the script
            self._scriptEndTime = time()
            self._scriptDuration = self._scriptEndTime - self._scriptStartTime

            self._errorOccurred = True

            # Not really an error, if it was sys.exit(0)
            excInfo = sys.exc_info()
            if excInfo[0] == SystemExit:
                code = excInfo[1].code
                if not code:
                    self._errorOccurred = False

            # Clean up
            if self._errorOccurred:
                if origDir:
                    os.chdir(origDir)
                    origDir = None

                # Handle exception
                self.handleException(sys.exc_info())

        self.deliver()

        # Restore original directory
        if origDir:
            os.chdir(origDir)

        # Note the duration of server processing (as late as we possibly can)
        self._serverDuration = time() - self._serverStartTime

        # Log it
        if self.setting('LogScripts'):
            self.writeScriptLog()

    def deliver(self):
        """Deliver the HTML.

        This is used for the output that came from the script being served,
        or from our own error reporting.
        """
        # Compile the headers & cookies
        headers = StringIO()
        for header, value in self._headers.items():
            headers.write("%s: %s\n" % (header, value))
        if 'cookies' in self._namespace:
            headers.write(str(self._namespace['cookies']))
        headers.write('\n')

        # Get the string buffer values
        headersOut = headers.getvalue()
        stdoutOut = sys.stdout.getvalue()

        # Compute size
        self._responseSize = len(headersOut) + len(stdoutOut)

        # Send to the real stdout
        self._realStdout.write(headersOut)
        self._realStdout.write(stdoutOut)


## Misc functions ##

def docType():
    """Return a standard HTML document type"""
    return ('<!DOCTYPE html>')


def htTitle(name):
    """Return an HTML section title."""
    return ('<h2 style="color:white;background-color:#993333;'
        'font-size:12pt;padding:1pt;font-weight:bold;'
        'font-family:Tahoma,Verdana,Arial,Helvetica,sans-serif;'
        'text-align:center">%s</h2>\n' % name)


def htDictionary(d, addSpace=None):
    """Returns an HTML table where each row is a key-value pair."""
    if not d:
        return '\n'
    html = ['<table>']
    for key in sorted(d):
        value = d[key]
        if addSpace is not None and key in addSpace:
            target = addSpace[key]
            value = (target + ' ').join(value.split(target))
        html.append('<tr><td style="background-color:#BBBBBB">%s</td>'
            '<td style="background-color:#EEEEEE">%s&nbsp;</td></tr>\n'
            % (key, value))
    html.append('</table>')
    return '\n'.join(html)


def htTable(listOfDicts, keys=None):
    """Return an HTML table for a list of dictionaries.

    The listOfDicts parameter is expected to be a list of
    dictionaries whose keys are always the same. This function
    returns an HTML string with the contents of the table.
    If keys is None, the headings are taken from the first row in
    alphabetical order.

    Returns an empty string if listOfDicts is none or empty.

    Deficiencies: There's no way to influence the formatting or to
    use column titles that are different from the keys.
    """
    if not listOfDicts:
        return ''
    if keys is None:
        keys = sorted(listOfDicts[0])
    html = ['<table>', '<tr>']
    for key in keys:
        html.append('<th style="background-color:#BBBBBB">%s</th>' % key)
    html.append('</tr>')
    for row in listOfDicts:
        html.append('<tr>')
        for key in keys:
            html.append(
                '<td style="background-color:#EEEEEE">%s</td>' % row[key])
        html.append('</tr>')
    html.append('</table>')
    return '\n'.join(html)


def osIdTable():
    """Get all OS id information.

    Returns a list of dictionaries containing id information such
    as uid, gid, etc., all obtained from the os module.

    Dictionary keys are 'name' and 'value'.
    """
    funcs = ['getegid', 'geteuid', 'getgid', 'getpgrp',
        'getpid', 'getppid', 'getuid']
    table = []
    for funcName in funcs:
        if hasattr(os, funcName):
            value = getattr(os, funcName)()
            table.append(dict(name=funcName, value=value))
    return table


def main():
    stdout = sys.stdout
    try:
        wrapper = CGIWrapper()
        wrapper.serve()
    except:
        # There is already a fancy exception handler in the CGIWrapper for
        # uncaught exceptions from target scripts. However, we should also
        # catch exceptions here that might come from the wrapper, including
        # ones generated while it's handling exceptions.
        sys.stderr.write('[%s] [error] CGI Wrapper: Error while executing'
            ' script (unknown)\n' % asctime(localtime()))
        traceback.print_exc(file=sys.stderr)
        if sys.exc_info()[0] != SystemExit:
            output = traceback.format_exception(*sys.exc_info())
            output = ''.join(output)
            output = output.replace('&', '&amp;').replace(
                '<', '&lt;').replace('>', '&gt;')
            stdout.write('''Content-Type: text/html

%s
<html>
<head><title>Error</title>
<body><h2>ERROR</h2>
<pre>%s</pre>
</body>
</html>
''' % (docType(), output))


if __name__ == '__main__':
    isMain = True
    main()
