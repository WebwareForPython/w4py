"""FieldStorage.py

This module defines a subclass of the standard Python cgi.FieldStorage class
with an extra method that will allow a FieldStorage to parse a query string
even in a POST request.
"""

import os
import cgi

from urllib import unquote


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
            environ=None, keep_blank_values=False, strict_parsing=False,
            max_num_fields=None, separator='&'):
        if environ is None:
            environ = os.environ
        method = environ.get('REQUEST_METHOD', 'GET').upper()
        qs_on_post = None if method in ('GET', 'HEAD') else environ.get(
            'QUERY_STRING', None)
        if qs_on_post:
            environ['QUERY_STRING'] = ''
        try:
            if headers is None:
                # work around Python issue 27777 in FieldStorage
                content_type = environ.get('CONTENT_TYPE')
                if (content_type and
                        content_type != 'application/x-www-form-urlencoded'
                        and not content_type.startswith('multipart/')):
                    if 'CONTENT_LENGTH' in environ:
                        headers = {'content-type': content_type,
                                   'content-length': '-1'}
            if separator == '&':
                if max_num_fields is None:
                    # max_num_fields is only supported since Python 2.7.16
                    cgi.FieldStorage.__init__(self, fp, headers, outerboundary,
                        environ, keep_blank_values, strict_parsing)
                else:
                    cgi.FieldStorage.__init__(self, fp, headers, outerboundary,
                        environ, keep_blank_values, strict_parsing,
                        max_num_fields)
            else:
                # separator is only supported in Python 2.7.18 with additional
                # vendor-supplied security patch (backported from Python 3)
                cgi.FieldStorage.__init__(self, fp, headers, outerboundary,
                    environ, keep_blank_values, strict_parsing,
                    max_num_fields, separator)
        finally:
            if qs_on_post:
                environ['QUERY_STRING'] = qs_on_post
        if qs_on_post:
            self.add_qs(qs_on_post)

    def add_qs(self, qs):
        """Add all non-existing parameters from the given query string."""
        # split the query string in the same way as the last Python 2 version
        try:
            max_num_fields = self.max_num_fields
        except AttributeError:
            max_num_fields = None
        try:
            separator = self.separator
        except AttributeError:
            # splitting algorithm in unpatched Python 2.7 and before
            if max_num_fields is not None:
                num_fields = 1 + qs.count('&') + qs.count(';')
                if max_num_fields < num_fields:
                    raise ValueError('Max number of fields exceeded')
            pairs = [s2 for s1 in qs.split('&') for s2 in s1.split(';')]
        else:
            # splitting algorithm in Python 2.7 with security patch
            if not separator or not isinstance(separator, basestring):
                raise ValueError("Separator must be a string.")
            if max_num_fields is not None:
                num_fields = 1 + qs.count(separator)
                if max_num_fields < num_fields:
                    raise ValueError('Max number of fields exceeded')
            pairs = [s1 for s1 in qs.split(separator)]
        if not pairs:
            return  # shortcut when there are no parameters
        if self.list is None:
            # This makes sure self.keys() are available, even
            # when valid POST data wasn't encountered.
            self.list = []
        append = self.list.append
        existing_names = set(self)
        strict_parsing = self.strict_parsing
        keep_blank_values = self.keep_blank_values
        for name_value in pairs:
            if not name_value and not strict_parsing:
                continue
            nv = name_value.split('=', 1)
            if len(nv) != 2:
                if strict_parsing:
                    raise ValueError("bad query field: %r" % (name_value,))
                # Handle case of a control-name with no equal sign
                if keep_blank_values:
                    nv.append('')
                else:
                    continue
            if len(nv[1]) or keep_blank_values:
                name = unquote(nv[0].replace('+', ' '))
                if name not in existing_names:
                    # Only append values that aren't already the FieldStorage;
                    # this makes POSTed vars override vars on the query string.
                    value = unquote(nv[1].replace('+', ' '))
                    append(cgi.MiniFieldStorage(name, value))
