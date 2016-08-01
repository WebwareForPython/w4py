import os
import unittest

import FixPath
from MiscUtils.DateParser import *


# To simplify testing, monkey-patch mx.DateTime
# so that its RangeErrors are also ValueErrors:
try:
    from mx.DateTime import RangeError
except ImportError:
    pass
else:
    RangeError.__bases__ += (ValueError,)


class TestDateTimeParser(unittest.TestCase):

    def testReturnType(self):
        from datetime import datetime
        self.assertTrue(type(parseDateTime(
            'Mon Jul 21 02:56:20 1969')) is datetime)

    def assertParses(self, s):
        self.assertEqual(parseDateTime(s).isoformat(), '1969-07-21T02:56:20')

    def testDefaultFormat(self):
        self.assertParses('Mon Jul 21 02:56:20 1969')

    def testCookieFormat(self):
        self.assertParses('Mon, 21-Jul-1969 02:56:20')

    def testISOFormat(self):
        self.assertParses('1969-07-21T02:56:20')

    def testShortISOFormat(self):
        self.assertParses('19690721T02:56:20')

    def testWrongFormat(self):
        self.assertRaises(ValueError, parseDateTime,
            'Mon Jul 21 02:56:20 19691')
        self.assertRaises(ValueError, parseDateTime,
            '19691')

    def testExternalParser(self):
        external = True
        try:
            from dateutil.parser import parse
        except ImportError:
            try:
                from mx.DateTime.Parser import DateTimeFromString
            except ImportError:
                external = False
        teststring = 'July 21, 1969, 2:56:20'
        if external:
            self.assertParses(teststring)
        else:
            self.assertRaises(ValueError, parseDateTime, teststring)


class TestDateParser(unittest.TestCase):

    def testReturnType(self):
        from datetime import date
        self.assertTrue(type(parseDate(
            'Mon Jul 21 02:56:20 1969')) is date)

    def assertParses(self, s):
        self.assertEqual(parseDate(s).isoformat(), '1969-07-21')

    def testDefaultFormat(self):
        self.assertParses('Mon Jul 21 02:56:20 1969')

    def testCookieFormat(self):
        self.assertParses('Mon, 21-Jul-1969 02:56:20')

    def testISOFormat(self):
        self.assertParses('1969-07-21T02:56:20')

    def testShortISOFormat(self):
        self.assertParses('19690721T02:56:20')
        self.assertParses('1969-07-21')
        self.assertParses('19690721')

    def testWrongFormat(self):
        self.assertRaises(ValueError, parseDateTime,
            'Mon Jul 21 02:56:20 19691')
        self.assertRaises(ValueError, parseDateTime,
            '19691')


class TestTimeParser(unittest.TestCase):

    def testReturnType(self):
        from datetime import time
        self.assertTrue(type(parseTime(
            'Mon Jul 21 02:56:20 1969')) is time)

    def assertParses(self, s):
        self.assertEqual(parseTime(s).isoformat(), '02:56:20')

    def testDefaultFormat(self):
        self.assertParses('Mon Jul 21 02:56:20 1969')

    def testCookieFormat(self):
        self.assertParses('Mon, 21-Jul-1969 02:56:20')

    def testISOFormat(self):
        self.assertParses('1969-07-21T02:56:20')

    def testShortISOFormat(self):
        self.assertParses('02:56:20')

    def testWrongFormat(self):
        self.assertRaises(ValueError, parseDateTime,
            'Mon Jul 21 02:65:20 1969')
        self.assertRaises(ValueError, parseDateTime,
            '02:65')


if __name__ == '__main__':
    unittest.main()
