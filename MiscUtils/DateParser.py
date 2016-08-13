"""DateParser.py

Convert string representations of dates to Python datetime objects.

Since this is not adequately supported by the Python standard library,
we try using the following third-party modules (in this order):

    python-dateutil: http://labix.org/python-dateutil
    mxDateTime: http://www.egenix.com/products/python/mxBase/mxDateTime/

If none of these modules are available, we try using the strptime function
in the Python standard library with several frequently used formats.

Contributed to Webware for Python by Christoph Zwerschke.
"""


try:
    from dateutil.parser import parse as parseDateTime

except ImportError:  # dateutil not available

    from datetime import datetime

    try:
        from mx.DateTime.Parser import DateTimeFromString

        def parseDateTime(s):
            t = DateTimeFromString(s)
            # needs to be converted to datetime
            try:
                return datetime.fromtimestamp(t)
            except Exception:  # out of range for timestamp values
                return datetime(*t.tuple()[:6])

    except ImportError:  # mx.DateTime not available

        strpdatetime = datetime.strptime

        def parseDateTime(s):
            """Return a datetime object corresponding to the given string."""
            formats = ("%a %b %d %H:%M:%S %Y", "%a, %d-%b-%Y %H:%M:%S",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
                "%Y%m%d %H:%M:%S", "%Y%m%dT%H:%M:%S",
                "%Y%m%d %H%M%S", "%Y%m%dT%H%M%S",
                "%m/%d/%y %H:%M:%S", "%Y-%m-%d %H:%M",
                "%Y-%m-%d", "%Y%m%d", "%m/%d/%y",
                "%H:%M:%S", "%H:%M", "%c")
            for format in formats:
                try:
                    return strpdatetime(s, format)
                except ValueError:
                    pass
            raise ValueError('Cannot parse date/time %s' % s)


def parseDate(s):
    """Return a date object corresponding to the given string."""
    return parseDateTime(s).date()


def parseTime(s):
    """Return a time object corresponding to the given string."""
    return parseDateTime(s).time()


__all__ = ['parseDateTime', 'parseDate', 'parseTime']
