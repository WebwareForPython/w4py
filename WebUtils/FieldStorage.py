"""FieldStorage.py

This module defines a subclass of the standard Python cgi.FieldStorage class
with an extra method that will allow a FieldStorage to parse a query string
even in a POST request.
"""

import cgi
import os
import urllib


class FieldStorage(cgi.FieldStorage):
    """Modified FieldStorage class for POST requests with query strings.

    Parameters in the query string which have not been sent via POST are
    appended to the field list. This is different from the behavior of
    Python versions before 2.6 which completely ignored the query string in
    POST request, but it's also different from the behavior of the later Python
    versions which append values from the query string to values sent via POST
    for parameters with the same name. With other words, our FieldStorage class
    overrides the query string parameters with the parameters sent via POST.

    As recommended by W3C in section B.2.2 of the HTML 4.01 specification,
    we also support use of ';' in place of '&' as separator in query strings.
    """

    def __init__(self, fp=None, headers=None, outerboundary='',
            environ=os.environ, keep_blank_values=False, strict_parsing=False):
        method = environ.get('REQUEST_METHOD', 'GET').upper()
        qs_on_post = (environ.get('QUERY_STRING', None)
            if method not in ('GET', 'HEAD') else None)
        if qs_on_post:
            environ['QUERY_STRING'] = ''
        try:
            cgi.FieldStorage.__init__(self, fp, headers, outerboundary,
                environ, keep_blank_values, strict_parsing)
        finally:
            if qs_on_post:
                environ['QUERY_STRING'] = qs_on_post
        if qs_on_post:
            self.add_qs(qs_on_post)

    def add_qs(self, qs):
        """Add all non-existing parameters from the given query string."""
        r = {}
        for name_value in qs.split('&'):
            for name_value in name_value.split(';'):
                nv = name_value.split('=', 2)
                if len(nv) != 2:
                    if self.strict_parsing:
                        raise ValueError('bad query field: %r' % (name_value,))
                    continue
                name = urllib.unquote(nv[0].replace('+', ' '))
                value = urllib.unquote(nv[1].replace('+', ' '))
                if len(value) or self.keep_blank_values:
                    if name in r:
                        r[name].append(value)
                    else:
                        r[name] = [value]
        if self.list is None:
            # This makes sure self.keys() are available, even
            # when valid POST data wasn't encountered.
            self.list = []
        for key in r:
            if key not in self:
                # Only append values that aren't already the FieldStorage;
                # this makes POSTed vars override vars on the query string.
                for value in r[key]:
                    self.list.append(cgi.MiniFieldStorage(key, value))
