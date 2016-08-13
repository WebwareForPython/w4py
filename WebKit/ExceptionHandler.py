"""Exception handling."""

import os
import sys
import poplib
import smtplib
import traceback
from random import randint
from time import time, localtime

from email.message import Message
from email.Utils import formatdate

from MiscUtils import StringIO
from MiscUtils.Funcs import asclocaltime
from WebUtils.HTMLForException import HTMLForException
from WebUtils.Funcs import htmlForDict, htmlEncode


class Singleton(object):
    """A singleton object."""


class ExceptionHandler(object):
    """Exception handling.

    ExceptionHandler is a utility class for Application that is created
    to handle a particular exception. The object is a one-shot deal.
    After handling an exception, it should be removed.

    At some point, the exception handler sends
    `writeExceptionReport` to the transaction (if present), which
    in turn sends it to the other transactional objects
    (application, request, response, etc.)  The handler is the
    single argument for this message.

    Classes may find it useful to do things like this::

        exceptionReportAttrs = 'foo bar baz'.split()
        def writeExceptionReport(self, handler):
            handler.writeTitle(self.__class__.__name__)
            handler.writeAttrs(self, self.exceptionReportAttrs)

    The handler write methods that may be useful are:

      * write
      * writeTitle
      * writeDict
      * writeAttrs

    Derived classes must not assume that the error occured in a
    transaction.  self._tra may be None for exceptions outside
    of transactions.

    **HOW TO CREATE A CUSTOM EXCEPTION HANDLER**

    In the ``__init__.py`` of your context::

        from WebKit.ExceptionHandler import ExceptionHandler as _ExceptionHandler

        class ExceptionHandler(_ExceptionHandler):

            _hideValuesForFields = _ExceptionHandler._hideValuesForFields + ['foo', 'bar']

            def work(self):
                _ExceptionHandler.work(self)
                # do whatever
                # override other methods if you like

        def contextInitialize(app, ctxPath):
            app._exceptionHandlerClass = ExceptionHandler

    You can also control the errors with settings in
    ``Application.config``
    """
    # keep these lower case to support case insensitivity:
    _hideValuesForFields = ['password', 'passwd', 'pwd',
        'creditcard', 'credit card', 'cc', 'pin', 'tan']
    if False:  # for testing
        _hideValuesForFields.extend(['application', 'uri',
            'http_accept', 'userid'])
    _hiddenString = '*** hidden ***'
    _addSpace = {'PATH': os.pathsep, 'CLASSPATH': os.pathsep,
        'HTTP_ACCEPT': ',', 'HTTP_ACCEPT_CHARSET': ',',
        'HTTP_ACCEPT_ENCODING': ',', 'HTTP_ACCEPT_LANGUAGE': ','}
    _docType = ('<!DOCTYPE HTML PUBLIC'
        ' "-//W3C//DTD HTML 4.01 Transitional//EN"'
        ' "http://www.w3.org/TR/html4/loose.dtd">')


    ## Init ##

    def __init__(self, application, transaction, excInfo,
            formatOptions=None):
        """Create an exception handler instance.

        ExceptionHandler instances are created anew for each exception.
        Instantiating ExceptionHandler completes the process --
        the caller need not do anything else.
        """
        # Keep references to the objects
        self._app = application
        self._tra = transaction
        self._exc = excInfo
        if self._tra:
            self._req = self._tra.request()
            self._res = self._tra.response()
        else:
            self._req = self._res = None

        self._formatOptions = formatOptions

        # Make some repairs, if needed. We use the transaction
        # & response to get the error page back out

        # @@ 2000-05-09 ce: Maybe a fresh transaction and
        # response should always be made for that purpose

        # @@ 2003-01-10 sd: This requires a transaction which
        # we do not have.

        # Making remaining code safe for no transaction.
        #
        # if self._res is None:
        #      self._res = HTTPResponse()
        #      self._tra.setResponse(self._res)

        # Cache MaxValueLengthInExceptionReport for speed
        self._maxValueLength = self.setting('MaxValueLengthInExceptionReport')

        # exception occurance time (overridden by response.endTime())
        self._time = time()

        # Get to work
        self.work()


    ## Accessors ##

    def setting(self, name):
        """Settings are inherited from Application."""
        return self._app.setting(name)

    def servletPathname(self):
        """The full filesystem path for the servlet."""
        try:
            return self._tra.request().serverSidePath()
        except Exception:
            return None

    def basicServletName(self):
        """The base name for the servlet (sans directory)."""
        name = self.servletPathname()
        if name is None:
            return 'unknown'
        else:
            return os.path.basename(name)


    ## Exception Handling ##

    def work(self):
        """Main error handling method.

        Invoked by `__init__` to do the main work. This calls
        `logExceptionToConsole`, then checks settings to see if it should
        call `saveErrorPage` (to save the error to disk) and `emailException`.

        It also sends gives a page from `privateErrorPage` or
        `publicErrorPage` (which one based on ``ShowDebugInfoOnErrors``).
        """
        if self._res:
            self._res.recordEndTime()
            self._time = self._res.endTime()

        self.logExceptionToConsole()

        # Write the error page out to the response if available:
        if self._res and (not self._res.isCommitted()
                or self._res.header('Content-Type', None) == 'text/html'):
            if not self._res.isCommitted():
                self._res.reset()
                self._res.setStatus(500, "Servlet Error")
            if self.setting('ShowDebugInfoOnErrors') == 1:
                publicErrorPage = self.privateErrorPage()
            else:
                publicErrorPage = self.publicErrorPage()
            self._res.write(publicErrorPage)

            # Add a large block comment; this prevents IE from overriding the
            # page with its own generic error 500 page
            self._res.write('<!-- - - - - - - - - - - - - - - - - - -->\n' * 100)

        privateErrorPage = None
        if self.setting('SaveErrorMessages'):
            privateErrorPage = self.privateErrorPage()
            filename = self.saveErrorPage(privateErrorPage)
        else:
            filename = None

        self.logExceptionToDisk(errorMsgFilename=filename)

        if self.setting('EmailErrors'):
            if privateErrorPage is None:
                privateErrorPage = self.privateErrorPage()
            try:
                self.emailException(privateErrorPage)
            except Exception, e:
                print "Could not send error email:", e

    def logExceptionToConsole(self, stderr=None):
        """Log an exception.

        Logs the time, servlet name and traceback to the console
        (typically stderr). This usually results in the information
        appearing in console/terminal from which AppServer was launched.
        """
        if stderr is None:
            stderr = sys.stderr
        stderr.write('[%s] [error] WebKit: Error while executing script %s\n'
            % (asclocaltime(self._time), self.servletPathname()))
        traceback.print_exc(file=stderr)

    def publicErrorPage(self):
        """Return a public error page.

        Returns a brief error page telling the user that an error has occurred.
        Body of the message comes from ``UserErrorMessage`` setting.
        """
        return '\n'.join((docType(), '<html>', '<head>', '<title>Error</title>',
            htStyle(), '</head>', '<body text="black" bgcolor="white">',
            htTitle('Error'), '<p>%s</p>' % self.setting('UserErrorMessage'),
            '</body>', '</html>\n'))

    def privateErrorPage(self):
        """Return a private error page.

        Returns an HTML page intended for the developer with
        useful information such as the traceback.

        Most of the contents are generated in `htmlDebugInfo`.
        """
        html = [docType(), '<html>', '<head>', '<title>Error</title>',
            htStyle(), '</head>', '<body text="black" bgcolor="white">',
            htTitle('Error'), '<p>%s</p>' % self.setting('UserErrorMessage')]
        html.append(self.htmlDebugInfo())
        html.extend(['</body>', '</html>\n'])
        return '\n'.join(html)

    def htmlDebugInfo(self):
        """Return the debug info.

        Return HTML-formatted debugging information about the current exception.
        Calls `writeHTML`, which uses ``self.write(...)`` to add content.
        """
        self._html = []
        self.writeHTML()
        html = ''.join(self._html)
        self._html = None
        return html

    def writeHTML(self):
        """Write the traceback.

        Writes all the parts of the traceback, invoking:
          * `writeTraceback`
          * `writeMiscInfo`
          * `writeTransaction`
          * `writeEnvironment`
          * `writeIds`
          * `writeFancyTraceback`
        """
        self.writeTraceback()
        self.writeMiscInfo()
        self.writeTransaction()
        self.writeEnvironment()
        self.writeIds()
        self.writeFancyTraceback()


    ## Write Methods ##

    def write(self, s):
        """Output `s` to the body."""
        self._html.append(str(s))

    def writeln(self, s):
        """Output `s` plus a newline."""
        self._html.append(str(s))
        self._html.append('\n')

    def writeTitle(self, s):
        """Output the sub-heading to define a section."""
        self.writeln(htTitle(s))

    def writeDict(self, d, heading=None, encoded=None):
        """Output a table-formated dictionary."""
        self.writeln(htmlForDict(d, addSpace=self._addSpace,
            filterValueCallBack=self.filterDictValue,
            maxValueLength=self._maxValueLength,
            topHeading=heading, isEncoded=encoded))

    def writeAttrs(self, obj, attrNames):
        """Output object attributes.

        Writes the attributes of the object as given by attrNames.
        Tries ``obj._name` first, followed by ``obj.name()``.
        Is resilient regarding exceptions so as not to spoil the
        exception report.
        """
        attrs = {}
        for name in attrNames:
            value = getattr(obj, '_' + name, Singleton)  # go for attribute
            try:
                if value is Singleton:
                    value = getattr(obj, name, Singleton)  # go for method
                    if value is Singleton:
                        value = '(could not find attribute or method)'
                    else:
                        try:
                            if callable(value):
                                value = value()
                            value = self.repr(value)
                        except Exception, e:
                            value = ('(exception during method call:'
                                ' %s: %s)' % (e.__class__.__name__, e))
                else:
                    value = self.repr(value)
            except Exception, e:
                value = ('(exception during value processing:'
                    ' %s: %s)' % (e.__class__.__name__, e))
            attrs[name] = value
        self.writeDict(attrs, ('Attribute', 'Value'), True)


    ## Traceback sections ##

    def writeTraceback(self):
        """Output the traceback.

        Writes the traceback, with most of the work done
        by `WebUtils.HTMLForException.HTMLForException`.
        """
        self.writeTitle('Traceback')
        self.write('<p><i>%s</i></p>' % self.servletPathname())
        self.write(HTMLForException(self._exc, self._formatOptions))

    def writeMiscInfo(self):
        """Output misc info.

        Write a couple little pieces of information about the environment.
        """
        self.writeTitle('MiscInfo')
        info = {
            'time':        asclocaltime(self._time),
            'filename':    self.servletPathname(),
            'os.getcwd()': os.getcwd(),
            'sys.path':    sys.path,
            'sys.version': sys.version,
        }
        self.writeDict(info)

    def writeTransaction(self):
        """Output transaction.

        Lets the transaction talk about itself, using
        `Transaction.writeExceptionReport`.
        """
        if self._tra:
            self._tra.writeExceptionReport(self)
        else:
            self.writeTitle("No current Transaction.")

    def writeEnvironment(self):
        """Output environment.

        Writes the environment this is being run in. This is *not* the
        environment that was passed in with the request (holding the CGI
        information) -- it's just the information from the environment
        that the AppServer is being executed in.
        """
        self.writeTitle('Environment')
        self.writeDict(os.environ)

    def writeIds(self):
        """Output OS identification.

        Prints some values from the OS (like processor ID).
        """
        self.writeTitle('OS Ids')
        self.writeDict(osIdDict(), ('Name', 'Value'))

    def writeFancyTraceback(self):
        """Output a fancy traceback, using CGITraceback."""
        if self.setting('IncludeFancyTraceback'):
            self.writeTitle('Fancy Traceback')
            try:
                from WebUtils.ExpansiveHTMLForException import (
                    ExpansiveHTMLForException)
                self.write(ExpansiveHTMLForException(
                    context=self.setting('FancyTracebackContext')))
            except Exception:
                self.write('<p>Unable to generate a fancy traceback'
                    ' (uncaught exception)!</p>')
                try:
                    self.write(HTMLForException(sys.exc_info()))
                except Exception:
                    self.write('<p>Unable to even generate a normal traceback'
                        ' of the exception in fancy traceback!</p>')

    def saveErrorPage(self, html):
        """Save the error page.

        Saves the given HTML error page for later viewing by
        the developer, and returns the filename used.
        """
        filename = os.path.join(self._app._errorMessagesDir,
            self.errorPageFilename())
        try:
            f = open(filename, 'w')
            try:
                f.write(html)
            finally:
                f.close()
        except IOError:
            sys.stderr.write('[%s] [error] WebKit: Cannot save error page (%s)\n'
                % (asclocaltime(self._time), filename))
        else:
            return filename

    def errorPageFilename(self):
        """Create filename for error page.

        Construct a filename for an HTML error page, not including the
        ``ErrorMessagesDir`` setting (which `saveError` adds on).
        """
        # Note: Using the timestamp and a random number is a poor technique
        # for filename uniqueness, but it is fast and good enough in practice.
        return 'Error-%s-%s-%06d.html' % (self.basicServletName(),
            '-'.join(map(lambda x: '%02d' % x, localtime(self._time)[:6])),
            randint(0, 999999))

    def logExceptionToDisk(self, errorMsgFilename=None):
        """Log the exception to disk.

        Writes a tuple containing (date-time, filename,
        pathname, exception-name, exception-data,error report
        filename) to the errors file (typically 'Errors.csv')
        in CSV format. Invoked by `handleException`.
        """
        if not self.setting('LogErrors'):
            return
        err, msg = self._exc[:2]
        if isinstance(err, basestring):  # string exception
            err, msg = '', str(msg or err)
        else:
            err, msg = err.__name__, str(msg)
        logline = (asclocaltime(self._time),
            self.basicServletName(), self.servletPathname(),
            err, msg, errorMsgFilename or '')
        def fixElement(element):
            element = str(element)
            if ',' in element or '"' in element:
                element = element.replace('"', '""')
                element = '"%s"' % element
            return element
        logline = map(fixElement, logline)
        filename = self._app.serverSidePath(self.setting('ErrorLogFilename'))
        if os.path.exists(filename):
            f = open(filename, 'a')
        else:
            f = open(filename, 'w')
            f.write('time,filename,pathname,exception name,'
                'exception data,error report filename\n')
        f.write(','.join(logline) + '\n')
        f.close()

    def emailException(self, htmlErrMsg):
        """Email the exception.

        Send the exception via mail, either as an attachment,
        or as the body of the mail.
        """
        message = Message()

        # Construct the message headers
        headers = self.setting('ErrorEmailHeaders').copy()
        headers['Date'] = formatdate()
        headers['Mime-Version'] = '1.0'
        headers['Subject'] = headers.get('Subject',
            '[WebKit Error]') + ' %s: %s' % sys.exc_info()[:2]
        for h, v in headers.items():
            if isinstance(v, (list, tuple)):
                v = ','.join(v)
            message.add_header(h, v)

        # Construct the message body
        if self.setting('EmailErrorReportAsAttachment'):
            # start off with a text/plain part
            text = ('WebKit caught an exception while processing'
                ' a request for "%s" at %s (timestamp: %s).'
                ' The plain text traceback from Python is printed below and'
                ' the full HTML error report from WebKit is attached.\n\n'
                    % (self.servletPathname(),
                        asclocaltime(self._time), self._time))
            message.set_type('multipart/mixed')
            part = Message()
            part.set_type('text/plain')
            body = StringIO()
            body.write(text)
            traceback.print_exc(file=body)
            part.set_payload(body.getvalue())
            body.close()
            message.attach(part)
            part = Message()
            # now add htmlErrMsg
            part.add_header('Content-Transfer-Encoding', '7bit')
            part.add_header('Content-Description',
                'HTML version of WebKit error message')
            part.add_header('Content-Disposition',
                'attachment', filename='WebKitErrorMsg.html')
            part.set_type('text/html')
            part.set_payload(htmlErrMsg)
            message.attach(part)
        else:
            message.set_type('text/html')
            message.set_payload(htmlErrMsg, 'us-ascii')

        # Send the message
        server = self.setting('ErrorEmailServer')
        # This setting can be: server, server:port, server:port:user:password
        # or server:port:user:password:popserver:popport for "smtp after pop".
        parts = server.split(':', 5)
        server = port = user = passwd = None
        popserver = popssl = popport = None
        try:
            server = parts[0]
            try:
                port = int(parts[1])
            except ValueError:
                pass
            user = parts[2]
            passwd = parts[3]
            popserver = parts[4]
            try:
                popport = int(parts[5])
            except ValueError:
                popport = None
            if parts[6].lower() == 'ssl':
                popssl = True
        except IndexError:
            pass
        if user and passwd and popserver:
            # SMTP after POP
            if popssl is None and popport == 995:
                popssl = True
            popssl = popssl and poplib.POP3_SSL or poplib.POP3
            if popport:
                popserver = popssl(popserver, popport)
            else:
                popserver = popssl(popserver)
            popserver.set_debuglevel(0)
            popserver.user(user)
            popserver.pass_(passwd)
            try:
                popserver.quit()
            except Exception:
                pass
        if port:
            server = smtplib.SMTP(server, port)
        else:
            server = smtplib.SMTP(server)
        try:
            server.set_debuglevel(0)
            if user and passwd and not popserver:
                # SMTP-AUTH
                server.ehlo()
                if server.has_extn('starttls'):
                    server.starttls()
                    server.ehlo()
                server.login(user, passwd)
            body = message.as_string()
            server.sendmail(headers['From'], headers['To'], body)
        finally:
            try:
                server.quit()
            except Exception:
                pass


    ## Filtering ##

    def filterDictValue(self, value, key, dict):
        """Filter dictionary values.

        Filters keys from a dict.  Currently ignores the
        dictionary, and just filters based on the key.
        """
        return self.filterValue(value, key)

    def filterValue(self, value, key):
        """Filter values.

        This is the core filter method that is used in all filtering.
        By default, it simply returns self._hiddenString if the key is
        in self._hideValuesForField (case insensitive). Subclasses
        could override for more elaborate filtering techniques.
        """
        try:
            key = key.lower()
        except Exception:
            pass
        if key in self._hideValuesForFields:
            return self._hiddenString
        else:
            return value


    ## Utility ##

    def repr(self, value):
        """Get HTML encoded representation.

        Returns the repr() of value already HTML encoded. As a special case,
        dictionaries are nicely formatted in table.

        This is a utility method for `writeAttrs`.
        """
        if isinstance(value, dict):
            return htmlForDict(value, addSpace=self._addSpace,
                filterValueCallBack=self.filterDictValue,
                maxValueLength=self._maxValueLength)
        else:
            rep = repr(value)
            if self._maxValueLength and len(rep) > self._maxValueLength:
                rep = rep[:self._maxValueLength] + '...'
            return htmlEncode(rep)


## Misc functions ##

def docType():
    """Return the document type for the page."""
    return ('<!DOCTYPE HTML PUBLIC'
        ' "-//W3C//DTD HTML 4.01 Transitional//EN"'
        ' "http://www.w3.org/TR/html4/loose.dtd">')


def htStyle():
    """Return the page style."""
    return ('''<style type="text/css">
<!--
body {
    background-color: white;
    color: #080810;
    font-size: 11pt;
    font-family: Tahoma,Verdana,Arial,Helvetica,sans-serif;
    margin: 0pt;
    padding: 8pt;
}
h2.section {
    font-size: 14pt;
    background-color:#933;
    color:white;
    text-align:center;
}
table.NiceTable {
    font-size: 10pt;
}
table.NiceTable td {
    background-color: #EEE;
    color: #111;
}
table.NiceTable th {
    background-color: #BBB;
    color: black;
}
table.NiceTable tr.TopHeading th {
    background-color: #555;
    color: white;
}
table.NiceTable table.NiceTable td {
    background-color: #DDD;
    color: #222;
}
table.NiceTable table.NiceTable th {
    background-color: #CCC;
    color: black;
    font-weight: normal;
}
-->
</style>''')


def htTitle(name):
    """Format a `name` as a section title."""
    return ('<h2 class="section">%s</h2>' % name)


def osIdDict():
    """Get all OS id information.

    Returns a dictionary containing id information such as

    """
    ids = ['egid', 'euid', 'gid', 'groups', 'pgrp',
        'pid', 'ppid', 'uid']
    attrs = {}
    for id in ids:
        getter = 'get' + id
        try:
            value = getattr(os, getter)()
            attrs[id] = value
        except AttributeError:
            pass
    return attrs
