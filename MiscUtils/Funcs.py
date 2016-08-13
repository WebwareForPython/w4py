"""MiscUtils.Funcs

This module holds functions that don't fit in anywhere else.

You can safely import * from MiscUtils.Funcs if you like.
"""

import os
import random
import datetime
import time
import textwrap

from struct import calcsize

from hashlib import md5, sha1

__all__ = [
    'commas', 'charWrap', 'wordWrap', 'excstr', 'hostName', 'localIP',
    'positiveId', 'safeDescription', 'asclocaltime', 'timestamp',
    'localTimeDelta', 'uniqueId', 'valueForString']


def commas(number):
    """Insert commas in a number.

    Return the given number as a string with commas to separate
    the thousands positions.

    The number can be a float, int, long or string. Returns None for None.
    """
    if number is None:
        return None
    if not number:
        return str(number)
    number = list(str(number))
    if '.' in number:
        i = number.index('.')
    else:
        i = len(number)
    while 1:
        i -= 3
        if i <= 0 or number[i - 1] == '-':
            break
        number.insert(i, ',')
    return ''.join(number)


def charWrap(s, width, hanging=0):
    """Word wrap a string.

    Return a new version of the string word wrapped with the given width
    and hanging indent. The font is assumed to be monospaced.

    This can be useful for including text between <pre> </pre> tags,
    since <pre> will not word wrap, and for lengthly lines,
    will increase the width of a web page.

    It can also be used to help delineate the entries in log-style
    output by passing hanging=4.
    """
    if not s:
        return s
    if hanging < 0 or width < 1 or hanging >= width:
        raise ValueError("Invalid width or indentation")
    hanging = ' ' * hanging
    lines = s.splitlines()
    i = 0
    while i < len(lines):
        s = lines[i]
        while len(s) > width:
            lines[i], s = s[:width].rstrip(), hanging + s[width:].lstrip()
            i += 1
            lines.insert(i, s)
        i += 1
    return '\n'.join(lines)


def wordWrap(s, width=78):
    """Return a version of the string word wrapped to the given width."""
    return textwrap.fill(s, width)


def excstr(e):
    """Return a string for the exception.

    The string will be in the format that Python normally outputs
    in interactive shells and such:
        <ExceptionName>: <message>
        AttributeError: 'object' object has no attribute 'bar'
    Neither str(e) nor repr(e) do that.
    """
    if e is None:
        return None
    return '%s: %s' % (e.__class__.__name__, e)


def hostName():
    """Return the host name.

    The name is taken first from the os environment and failing that,
    from the 'hostname' executable. May return None if neither attempt
    succeeded. The environment keys checked are HOST and HOSTNAME,
    both upper and lower case.
    """
    for name in ['HOST', 'HOSTNAME', 'host', 'hostname']:
        hostName = os.environ.get(name)
        if hostName:
            break
    if not hostName:
        hostName = os.popen('hostname').read().strip()
    if not hostName:
        hostName = None
    else:
        hostName = hostName.lower()
    return hostName


_localIP = None

def localIP(remote=('www.yahoo.com', 80), useCache=True):
    """Get the "public" address of the local machine.

    This is the address which is connected to the general Internet.

    This function connects to a remote HTTP server the first time it is
    invoked (or every time it is invoked with useCache=0). If that is
    not acceptable, pass remote=None, but be warned that the result is
    less likely to be externally visible.

    Getting your local ip is actually quite complex. If this function
    is not serving your needs then you probably need to think deeply
    about what you really want and how your network is really set up.
    Search comp.lang.python for "local ip" for more information.
    http://groups.google.com/groups?q=%22local+ip%22+group:comp.lang.python.*
    """
    global _localIP
    if useCache and _localIP:
        return _localIP
    import socket
    if remote:
        # code from Donn Cave on comp.lang.python
        #
        # My notes:
        # Q: Why not use this? socket.gethostbyname(socket.gethostname())
        # A: On some machines, it returns '127.0.0.1' - not what we had in mind.
        #
        # Q: Why not use this? socket.gethostbyname_ex(socket.gethostname())[2]
        # A: Because some machines have more than one IP (think "VPN", etc.) and
        #    there is no easy way to tell which one is the externally visible IP.
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(remote)
            address, port = s.getsockname()
            s.close()
            if address and not address.startswith('127.'):
                if useCache:
                    _localIP = address
                return address
        except socket.error:
            # oh, well. we'll use the local method
            pass
    addresses = socket.gethostbyname_ex(socket.gethostname())[2]
    for address in addresses:
        if address and not address.startswith('127.'):
            if useCache:
                _localIP = address
            return address
    if useCache:
        _localIP = addresses[0]
    return _localIP


# Addresses can "look negative" on some boxes, some of the time.
# If you feed a "negative address" to an %x format, modern Python
# versions will display it as signed. So when you want to produce
# an address, use positiveId() to obtain it.
# _address_mask is 2**(number_of_bits_in_a_native_pointer).
# Adding this to a negative address gives a positive int with the same
# hex representation as the significant bits in the original.
# This idea and code were taken from ZODB (http://svn.zope.org).

_address_mask = 256L ** calcsize('P')


def positiveId(obj):
    """Return id(obj) as a non-negative integer."""
    result = id(obj)
    if result < 0:
        result += _address_mask
        assert result > 0
    return result


def _descExc(reprOfWhat, err):
    """Return a description of an exception.

    This is a private function for use by safeDescription().
    """
    try:
        return '(exception from repr(%s): %s: %s)' % (
            reprOfWhat, err.__class__.__name__, err)
    except Exception:
        return '(exception from repr(%s))' % reprOfWhat


def safeDescription(obj, what='what'):
    """Return the repr() of obj and its class (or type) for help in debugging.

    A major benefit here is that exceptions from repr() are consumed.
    This is important in places like "assert" where you don't want
    to lose the assertion exception in your attempt to get more information.

    Example use:
    assert isinstance(foo, Foo), safeDescription(foo)
    print "foo:", safeDescription(foo)  # won't raise exceptions

    # better output format:
    assert isinstance(foo, Foo), safeDescription(foo, 'foo')
    print safeDescription(foo, 'foo')
    """
    try:
        xRepr = repr(obj)
    except Exception as e:
        xRepr = _descExc('obj', e)
    if hasattr(obj, '__class__'):
        try:
            cRepr = repr(obj.__class__)
        except Exception as e:
            cRepr = _descExc('obj.__class__', e)
        return '%s=%s class=%s' % (what, xRepr, cRepr)
    else:
        try:
            cRepr = repr(type(obj))
        except Exception as e:
            cRepr = _descExc('type(obj)', e)
        return '%s=%s type=%s' % (what, xRepr, cRepr)


def asclocaltime(t=None):
    """Return a readable string of the current, local time.

    Useful for time stamps in log files.
    """
    return time.asctime(time.localtime(t))


def timestamp(t=None):
    """Return a dictionary whose keys give different versions of the timestamp.

    The dictionary will contain the following timestamp versions:
        'tuple': (year, month, day, hour, min, sec)
        'pretty': 'YYYY-MM-DD HH:MM:SS'
        'condensed': 'YYYYMMDDHHMMSS'
        'dashed': 'YYYY-MM-DD-HH-MM-SS'

    The focus is on the year, month, day, hour and second, with no additional
    information such as timezone or day of year. This form of timestamp is
    often ideal for print statements, logs and filenames. If the current number
    of seconds is not passed, then the current time is taken. The 'pretty'
    format is ideal for print statements, while the 'condensed' and 'dashed'
    formats are generally more appropriate for filenames.
    """
    t = time.localtime(t)[:6]
    return dict(tuple=t,
        pretty='%4i-%02i-%02i %02i:%02i:%02i' % t,
        condensed='%4i%02i%02i%02i%02i%02i' % t,
        dashed='%4i-%02i-%02i-%02i-%02i-%02i' % t)


def localTimeDelta(t=None):
    """Return timedelta of local zone from GMT."""
    if t is None:
        t = time.time()
    dt = datetime.datetime
    return dt.fromtimestamp(t) - dt.utcfromtimestamp(t)


def uniqueId(forObject=None, sha=False):
    """Generate an opaque, identifier string.

    The string is practically guaranteed to be unique
    If an object is passed, then its id() is incorporated into the generation.
    Returns a 32 character long string relying on md5 or,
    if sha is True, a 40 character long string relying on sha-1.
    """
    try:  # prefer os.urandom(), if available
        r = [os.urandom(8)]
    except (AttributeError, NotImplementedError):
        r = [time.time(), random.random(), os.times()]
    if forObject is not None:
        r.append(id(forObject))
    return (sha1 if sha else md5)(str(r)).hexdigest()


def valueForString(s):
    """Return value for a string.

    For a given string, returns the most appropriate Pythonic value
    such as None, a long, an int, a list, etc. If none of those
    make sense, then returns the string as-is.

    "None", "True" and "False" are case-insensitive because there is
    already too much case sensitivity in computing, damn it!
    """
    if not s:
        return s
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return long(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    t = s.lower()
    if t == 'none':
        return None
    if t.lower() == 'true':
        return True
    if t.lower() == 'false':
        return False
    if s[0] in '[({"\'':
        return eval(s)
    return s
