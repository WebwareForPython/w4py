"""HTTP responses"""

from datetime import datetime, timedelta
from time import time, gmtime, strftime, struct_time

from MiscUtils import NoDefault
from MiscUtils.DateInterval import timeDecode
from MiscUtils.Funcs import localTimeDelta

from Response import Response
from Cookie import Cookie
from HTTPExceptions import HTTPException, HTTPServerError

debug = False


class HTTPResponse(Response):


    ## Init ##

    def __init__(self, transaction, strmOut, headers=None):
        """Initialize the request."""

        Response.__init__(self, transaction, strmOut)

        self._committed = False

        if headers is None:
            self._headers = {}
            self.setHeader('Content-Type', 'text/html')
        else:
            self._headers = headers

        self._cookies = {}


    ## Protocol ##

    def protocol(self):
        """Return the name and version of the protocol."""
        return self._transaction.request().protocol()


    ## Headers ##

    def header(self, name, default=NoDefault):
        """Return the value of the specified header."""
        if default is NoDefault:
            return self._headers[name.capitalize()]
        else:
            return self._headers.get(name.capitalize(), default)

    def hasHeader(self, name):
        return name.capitalize() in self._headers

    def setHeader(self, name, value):
        """Set a specific header by name.

        Parameters:
            name: the header name
            value: the header value
        """
        assert not self._committed, "Headers have already been sent."
        self._headers[name.capitalize()] = value

    def headers(self, name=None):
        """Return all the headers.

        Returns a dictionary-style object of all header objects contained by
        this request.
        """
        return self._headers

    def clearHeaders(self):
        """Clear all the headers.

        You might consider a setHeader('Content-Type', 'text/html')
        or something similar after this.
        """
        assert not self._committed, "Headers have already been sent."
        self._headers = {}


    ## Cookies ##

    def cookie(self, name):
        """Return the value of the specified cookie."""
        return self._cookies[name]

    def hasCookie(self, name):
        """Return True if the specified cookie is present."""
        return name in self._cookies

    def setCookie(self, name, value, path='/', expires='ONCLOSE',
            secure=False):
        """Set a cookie.

        You can also set the path (which defaults to /).
        You can also set when it expires. It can expire:
          'NOW': this is the same as trying to delete it, but it
            doesn't really seem to work in IE
          'ONCLOSE': the default behavior for cookies (expires when
            the browser closes)
          'NEVER': some time in the far, far future.
          integer: a timestamp value
          tuple or struct_time: a tuple, as created by the time module
          datetime: a datetime.datetime object for the time (if without
            time zone, assumed to be *local*, not GMT time)
          timedelta: a duration counted from the present, e.g.,
            datetime.timedelta(days=14) (2 weeks in the future)
          '+...': a time in the future, '...' should be something like
            1w (1 week), 3h46m (3:45), etc.  You can use y (year),
            b (month), w (week), d (day), h (hour), m (minute),
            s (second). This is done by the MiscUtils.DateInterval.
        """
        cookie = Cookie(name, value)
        t = expires
        if isinstance(t, basestring):
            if t == 'ONCLOSE':
                t = None
            elif t == 'NOW':
                cookie.delete()
                return
            elif t == 'NEVER':
                t = gmtime()
                t = (t[0] + 10,) + t[1:]
            elif t.startswith('+'):
                t = time() + timeDecode(t[1:])
        if t:
            if isinstance(t, (int, long, float)):
                t = gmtime(t)
            if isinstance(t, (tuple, struct_time)):
                t = strftime("%a, %d-%b-%Y %H:%M:%S GMT", t)
            if isinstance(t, timedelta):
                t = datetime.now() + t
            if isinstance(t, datetime):
                d = t.utcoffset()
                if d is None:
                    d = localTimeDelta()
                t -= d
                t = t.strftime("%a, %d-%b-%Y %H:%M:%S GMT")
            cookie.setExpires(t)
        if path:
            cookie.setPath(path)
        if secure:
            cookie.setSecure(secure)
        self.addCookie(cookie)

    def addCookie(self, cookie):
        """Add a cookie that will be sent with this response.

        cookie is a Cookie object instance. See WebKit.Cookie.
        """
        assert not self._committed, "Headers have already been sent."
        assert isinstance(cookie, Cookie)
        self._cookies[cookie.name()] = cookie

    def delCookie(self, name, path='/', secure=False):
        """Delete a cookie at the browser.

        To do so, one has to create and send to the browser a cookie with
        parameters that will cause the browser to delete it.
        """
        if name in self._cookies:
            self._cookies[name].delete()
        else:
            cookie = Cookie(name, None)
            if path:
                cookie.setPath(path)
            if secure:
                cookie.setSecure(secure)
            cookie.delete()
            self.addCookie(cookie)

    def cookies(self):
        """Get all the cookies.

        Returns a dictionary-style object of all Cookie objects that will
        be sent with this response.
        """
        return self._cookies

    def clearCookies(self):
        """Clear all the cookies."""
        assert not self._committed, "Headers have already been sent."
        self._cookies = {}


    ## Status ##

    def setStatus(self, code, msg=''):
        """Set the status code of the response, such as 200, 'OK'."""
        assert not self._committed, "Headers have already been sent."
        self.setHeader('Status', str(code) + ' ' + msg)


    ## Special responses ##

    def sendError(self, code, msg=''):
        """Set the status code to the specified code and message."""
        assert not self._committed, "Response already partially sent."
        self.setStatus(code, msg)

    def sendRedirect(self, url, status=None):
        """Redirect to another url.

        This method sets the headers and content for the redirect, but does
        NOT change the cookies. Use clearCookies() as appropriate.

        See http://www.ietf.org/rfc/rfc2616 (section 10.3.3),
        http://www.ietf.org/rfc/rfc3875 (section 6.2.3) and
        http://support.microsoft.com/kb/176113
        (removing cookies by IIS is considered a bug).
        """
        assert not self._committed, "Headers have already been sent."
        self.setHeader('Status', status or '302 Found')
        self.setHeader('Location', url)
        self.setHeader('Content-Type', 'text/html')
        self.write('<html><body>This page has been redirected'
            ' to <a href="%s">%s</a>.</body></html>' % (url, url))

    def sendRedirectPermanent(self, url):
        """Redirect permanently to another URL."""
        self.sendRedirect(url, status='301 Moved Permanently')

    def sendRedirectSeeOther(self, url):
        """Redirect to a URL that shall be retrieved with GET.

        This method exists primarily to allow for the PRG pattern.
        See http://en.wikipedia.org/wiki/Post/Redirect/Get
        """
        self.sendRedirect(url, status='303 See Other')

    def sendRedirectTemporary(self, url):
        """Redirect temporarily to another URL."""
        self.sendRedirect(url, status='307 Temporary Redirect')


    ## Output ##

    def write(self, charstr=None):
        """Write charstr to the response stream.

        charstr must be convertible into an ordinary string.
        Unicode strings with special characters must therefore
        be encoded before they can be written.
        """
        if charstr:
            self._strmOut.write(str(charstr))
        if not self._committed and self._strmOut._needCommit:
            self.commit()

    def flush(self, autoFlush=True):
        """Send all accumulated response data now.

        Commits the response headers and tells the underlying stream to flush.
        if autoFlush is true, the responseStream will flush itself automatically
        from now on.

        Caveat: Some webservers, especially on Win, will still buffer the output
        from your servlet until it terminates before transmitting the results
        to the browser. Also, server modules for Apache like mod_deflate or
        mod_gzip may do buffering of their own that will cause flush() to not
        result in data being sent immediately to the client. You can prevent
        this by setting a no-gzip note in the Apache configuration, e.g.

           SetEnvIf Request_URI ^/wk/MyServlet no-gzip=1

        Even the browser may buffer its input before displaying it. For example,
        Netscape buffered text until it received an end-of-line or the beginning
        of a tag, and it didn't render tables until the end tag of the outermost
        table was seen. Some Firefox add-ons also buffer response data before it
        gets rendered. Some versions of MSIE will only start to display the page
        after they have received 256 bytes of output, so you may need to send
        extra whitespace before flushing to get MSIE to display the page.
        """
        if not self._committed:
            self.commit()
        self._strmOut.flush()
        self._strmOut.setAutoCommit(autoFlush)

    def isCommitted(self):
        """Check whether response is already commited.

        Checks whether the response has already been partially or completely sent.
        If this returns true, no new headers/cookies can be added
        to the response.
        """
        return self._committed

    def deliver(self):
        """Deliver response.

        The final step in the processing cycle.
        Not used for much with responseStreams added.
        """
        if debug:
            print "HTTPResponse deliver called"
        self.recordEndTime()
        if not self._committed:
            self.commit()

    def commit(self):
        """Commit response.

        Write out all headers to the response stream, and tell the underlying
        response stream it can start sending data.
        """
        if debug:
            print "HTTPResponse commit"
        self.recordSession()
        if self._transaction.errorOccurred():
            err = self._transaction.error()
            if not isinstance(err, HTTPException):
                err = HTTPServerError()
                self._transaction.setError(err)
            self.setErrorHeaders(err)
        self.writeHeaders()
        self._committed = True
        self._strmOut.commit()

    def writeHeaders(self):
        """Write headers to the response stream. Used internally."""
        if self._committed:
            print "response.writeHeaders called when already committed"
            return
        # make sure the status header comes first
        if 'Status' in self._headers:
            # store and temporarily delete status
            status = self._headers['Status']
            del self._headers['Status']
        else:
            # invent meaningful status
            status = '302 Found' if 'Location' in self._headers else '200 OK'
        head = ['Status: %s' % status]
        head.extend(map(lambda h: '%s: %s' % h, self._headers.items()))
        self._headers['Status'] = status  # restore status
        head.extend(map(lambda c: 'Set-Cookie: %s' % c.headerValue(),
            self._cookies.values()))
        head.extend(['']*2)  # this adds one empty line
        head = '\r\n'.join(head)
        self._strmOut.prepend(head)

    def recordSession(self):
        """Record session ID.

        Invoked by commit() to record the session ID in the response
        (if a session exists). This implementation sets a cookie for
        that purpose. For people who don't like sweets, a future version
        could check a setting and instead of using cookies, could parse
        the HTML and update all the relevant URLs to include the session ID
        (which implies a big performance hit). Or we could require site
        developers to always pass their URLs through a function which adds
        the session ID (which implies pain). Personally, I'd rather just
        use cookies. You can experiment with different techniques by
        subclassing Session and overriding this method. Just make sure
        Application knows which "session" class to use.

        It should be also considered to automatically add the server port
        to the cookie name in order to distinguish application instances
        running on different ports on the same server, or to use the port
        cookie-attribute introduced with RFC 2965 for that purpose.
        """
        trans = self._transaction
        app = trans.application()
        if not app.setting('UseCookieSessions'):
            return
        session = trans._session
        if not session:
            if debug:
                print '>> recordSession: Did not set SID.'
            return
        request = trans.request()
        sessionName = app.sessionName(trans)
        identifier = session.identifier()
        if session.isExpired() or session.timeout() == 0:
            self.delCookie(sessionName, app.sessionCookiePath(trans),
                request.isSecure() and app.setting('SecureSessionCookie'))
            if debug:
                print '>> recordSession: Removing SID', identifier
            return
        if request.hasCookie(sessionName):
            if request.cookie(sessionName) == identifier:
                if debug:
                    print '>> recordSession: Using SID', identifier
                return
        cookie = Cookie(app.sessionName(trans), identifier)
        cookie.setPath(app.sessionCookiePath(trans))
        if trans.request().isSecure():
            cookie.setSecure(app.setting('SecureSessionCookie'))
        self.addCookie(cookie)
        if debug:
            print '>> recordSession: Setting SID', identifier

    def reset(self):
        """Reset the response (such as headers, cookies and contents)."""
        assert not self._committed, \
            "Cannot reset the response; it has already been sent."
        self._headers = {}
        self.setHeader('Content-Type', 'text/html')
        self._cookies = {}
        self._strmOut.clear()

    def rawResponse(self):
        """Return the final contents of the response.

        Don't invoke this method until after deliver().

        Returns a dictionary representing the response containing only
        strings, numbers, lists, tuples, etc. with no backreferences.
        That means you don't need any special imports to examine the contents
        and you can marshal it. Currently there are two keys. 'headers' is
        list of tuples each of which contains two strings: the header and
        it's value. 'contents' is a string (that may be binary, for example,
        if an image were being returned).
        """
        headers = []
        for key, value in self._headers.items():
            headers.append((key, value))
        for cookie in self._cookies.values():
            headers.append(('Set-Cookie', cookie.headerValue()))
        return dict(headers=headers, contents=self._strmOut.buffer())

    def size(self):
        """Return the size of the final contents of the response.

        Don't invoke this method until after deliver().
        """
        return self._strmOut.size()

    def mergeTextHeaders(self, headerstr):
        """Merge text into our headers.

        Given a string of headers (separated by newlines),
        merge them into our headers.
        """
        lines = headerstr.splitlines()
        for line in lines:
            header = line.split(':', 1)
            if len(header) > 1:
                self.setHeader(header[0], header[1].rstrip())


    ## Exception reporting ##

    _exceptionReportAttrNames = Response._exceptionReportAttrNames + [
        'committed', 'headers', 'cookies']

    def setErrorHeaders(self, err):
        """Set error headers for an HTTPException."""
        for header, value in err.headers().items():
            self.setHeader(header, value)
        self.setStatus(err.code(), err.codeMessage())
        self.setHeader('Content-Type', 'text/html')

    def displayError(self, err):
        """Display HTTPException errors, with status codes."""
        assert not self._committed, "Already committed"
        self._strmOut.clear()
        self._strmOut.write(err.html())
        uri = self._transaction.request().uri()
        print 'HTTPResponse: %s: %s' % (uri, err.codeMessage())
        self.commit()
