"""HTMLForException.py

Create HTML for exceptions.
"""

import os
import re
import sys
import traceback
import urllib

from Funcs import htmlEncode


HTMLForExceptionOptions = {
    'table': 'background-color:#F0F0F0',
    'default': 'color:#000000',
    'row.location': 'color:#000099',
    'row.code': 'color:#990000',
    'editlink': None,
}


fileRE = re.compile(r'File "([^"]*)", line ([0-9]+), in ([^ ]*)')

def HTMLForLines(lines, options=None):
    """Create HTML for exceptions and tracebacks from a list of strings."""

    # Set up the options:
    if options:
        opt = HTMLForExceptionOptions.copy()
        opt.update(options)
    else:
        opt = HTMLForExceptionOptions

    # Create the HTML:
    res = ['<table style="width:100%%;%s">\n' % opt['table'],
        '<tr><td><pre style="%s">\n' % opt['default']]
    for line in lines:
        match = fileRE.search(line)
        if match:
            parts = map(htmlEncode, line.split('\n', 2))
            parts[0] = '<span style="%s">%s</span>' % (
                opt['row.location'], parts[0])
            if opt['editlink']:
                parts[0] = ('%s <a href="%s?filename=%s&amp;line=%s">[edit]</a>'
                    % (parts[0], opt['editlink'], urllib.quote(
                        os.path.abspath(match.group(1))), match.group(2)))
            parts[1] = '<span style="%s">%s</span>' % (
                opt['row.code'], parts[1])
            line = '\n'.join(parts)
            res.append(line)
        else:
            res.append(htmlEncode(line))
    if lines:
        if res[-1][-1] == '\n':
            res[-1] = res[-1].rstrip()
    res.extend(['</pre></td></tr>\n', '</table>\n'])
    return ''.join(res)


def HTMLForStackTrace(frame=None, options=None):
    """Get HTML for displaying a stack trace.

    Returns an HTML string that presents useful information to the developer
    about the stack. The first argument is a stack frame such as returned by
    sys._getframe() which is in fact invoked if a stack frame isn't provided.
    """

    # Get the stack frame if needed:
    if frame is None:
        frame = sys._getframe()

    # Return formatted stack traceback
    return HTMLForLines(traceback.format_stack(frame), options)


def HTMLForException(excInfo=None, options=None):
    """Get HTML for displaying an exception.

    Returns an HTML string that presents useful information to the developer
    about the exception. The first argument is a tuple such as returned by
    sys.exc_info() which is in fact invoked if the tuple isn't provided.
    """

    # Get the excInfo if needed:
    if excInfo is None:
        excInfo = sys.exc_info()

    # Return formatted exception traceback
    return HTMLForLines(traceback.format_exception(*excInfo), options)
