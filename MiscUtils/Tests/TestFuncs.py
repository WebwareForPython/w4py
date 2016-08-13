import time
import unittest

import FixPath
from MiscUtils.Funcs import *


class TestFuncs(unittest.TestCase):
    """Unit tests for the functions in MiscUtils.Funcs."""

    def testCommas(self):
        testSpec = '''
            0 '0'
            0.0 '0.0'
            1 '1'
            11 '11'
            111 '111'
            1111 '1,111'
            11111 '11,111'
            1.0 '1.0'
            11.0 '11.0'
            1.15 '1.15'
            12345.127 '12,345.127'
            -1 '-1'
            -11 '-11'
            -111 '-111'
            -1111 '-1,111'
            -11111 '-11,111'
        '''
        tests = testSpec.split()
        count = len(tests)
        i = 0
        while i < count:
            source = eval(tests[i])
            result = eval(tests[i+1])
            #print '%r yields %r' % (source, result)
            self.assertEqual(commas(source), result)
            # Now try the source as a string instead of a number:
            source = eval("'%s'" % tests[i])
            #print '%r yields %r' % (source, result)
            self.assertEqual(commas(source), result)
            i += 2

    def testCharWrap(self):
        self.assertEqual(charWrap("""
            Sparse is better than dense.
            Readability counts.""", 34, 16), """
            Sparse is better than
                dense.
            Readability counts.""")

    def testWordWrap(self):
        # an example with some spaces and newlines
        msg = """Arthur:  "The Lady of the Lake, her arm clad in the purest \
shimmering samite, held aloft Excalibur from the bosom of the water, \
signifying by Divine Providence that I, Arthur, was to carry \
Excalibur. That is why I am your king!"

Dennis:  "Listen. Strange women lying in ponds distributing swords is \
no basis for a system of government. Supreme executive power derives \
from a mandate from the masses, not from some farcical aquatic \
ceremony!\""""

        for margin in range(20, 200, 29):
            if margin == 78:
                s = wordWrap(msg)
            else:
                s = wordWrap(msg, margin)
            for line in s.splitlines():
                self.assertTrue(len(line) <= margin,
                    'len=%i, margin=%i, line=%r' % (len(line), margin, line))
            self.assertEqual(msg.split(), s.split())

    def testExcstr(self):
        self.assertEqual(excstr(None), None)
        self.assertEqual(excstr(ValueError('Kawoom!')),
            'ValueError: Kawoom!')

    def testHostName(self):
        # About all we can do is invoke hostName() to see that no exceptions
        # are thrown, and do a little type checking on the return type.
        host = hostName()
        self.assertTrue(host is None or isinstance(host, str),
            'host type = %s, host = %s' % (type(host), repr(host)))

    def testLocalIP(self):
        ip = localIP()
        self.assertTrue(ip)
        self.assertFalse(ip.startswith('127.'))
        self.assertEqual(localIP(), ip)  # second invocation
        self.assertEqual(localIP(useCache=None), ip)
        self.assertEqual(localIP(remote=None, useCache=None), ip,
            'See if this works: localIP(remote=None).'
            ' If this fails, dont worry.')
        self.assertEqual(localIP(
            remote=('www.aslkdjsfliasdfoivnoiedndfgncvb.com', 80),
            useCache=None), ip)  # not existing remote address

    def testPositiveId(self):
        # About all we can do is invoke positiveId()
        # to see that no exceptions are thrown and the result is positive.
        self.assertTrue(positiveId(self) > 0)

    def testSafeDescription(self):
        sd = safeDescription

        # basics:
        s = sd(1).replace('type=', 'class=')
        self.assertEqual(s, "what=1 class=<type 'int'>")
        s = sd(1, 'x').replace('type=', 'class=')
        self.assertEqual(s, "x=1 class=<type 'int'>")
        s = sd('x').replace('type=', 'class=')
        s = s.replace("<type 'string'>", "<type 'str'>")
        self.assertEqual(s, "what='x' class=<type 'str'>")

        class OldStyle:
            pass
        old = OldStyle()
        self.assertTrue('%s.OldStyle' % __name__ in sd(old))

        class NewStyle(object):
            pass
        new = NewStyle()
        self.assertTrue('%s.NewStyle' % __name__ in sd(new))

        # okay now test that safeDescription eats exceptions from repr():
        class Bogus(object):
            def __repr__(self):
                raise KeyError('bogus')
        b = Bogus()
        try:
            s = sd(b)
        except Exception:
            s = 'failure: should not throw exception'
        self.assertTrue("(exception from repr(obj): KeyError: 'bogus')" in s)

    def testAsclocaltime(self):
        self.assertEqual(len(asclocaltime()), 24)
        t = time.time()
        self.assertEqual(asclocaltime(t), time.asctime(time.localtime(t)))

    def testTimestamp(self):
        d = timestamp()
        self.assertTrue(isinstance(d, dict))
        self.assertEqual(','.join(sorted(d)), 'condensed,dashed,pretty,tuple')
        self.assertEqual(len(d['tuple']), 6)
        self.assertEqual(len(d['condensed']), 14)
        self.assertEqual(len(d['pretty']), 19)
        self.assertEqual(len(d['dashed']), 19)
        t = time.time()
        d = timestamp(t)
        t = time.localtime(t)[:6]
        self.assertEqual(d['tuple'], t)
        self.assertEqual(d['condensed'], '%4i%02i%02i%02i%02i%02i' % t)
        self.assertEqual(d['condensed'],
            d['pretty'].replace('-', '').replace(':', '').replace(' ', ''))
        self.assertEqual(d['condensed'], d['dashed'].replace('-', ''))

    def testLocalTimeDelta(self):
        d = localTimeDelta()
        self.assertEqual(d.microseconds, 0)
        self.assertEqual(d.seconds % 3600, 0)
        self.assertTrue(-1 <= d.days < 1)
        d = localTimeDelta(time.time())
        self.assertEqual(d.microseconds, 0)
        self.assertEqual(d.seconds % 3600, 0)
        self.assertTrue(-1 <= d.days < 1)

    def testUniqueId(self):

        def checkId(i, sha, past):
            self.assertTrue(isinstance(i, str), type(i))
            self.assertEqual(len(i), 40 if sha else 32)
            for c in i:
                self.assertTrue(c in '0123456789abcdef')
            self.assertFalse(i in past)
            past[i] = i

        for sha in (False, True):
            past = {}
            for n in range(10):
                if sha:
                    checkId(uniqueId(None, True), True, past)
                    checkId(uniqueId(n, True), True, past)
                else:
                    checkId(uniqueId(None, False), False, past)
                    checkId(uniqueId(n, False), False, past)
                checkId(uniqueId(sha=sha), sha, past)
                checkId(uniqueId(n, sha=sha), sha, past)
                checkId(uniqueId(forObject=checkId, sha=sha), sha, past)

    def testValueForString(self):
        evalCases = '''
            1
            5L
            5.5
            True
            False
            None
            [1]
            ['a']
            {'x':1}
            (1, 2, 3)
            'a'
            "z"
            """1234"""
        '''

        stringCases = '''
            kjasdfkasdf
            2389234lkdsflkjsdf
            *09809
        '''

        evalCases = [s.strip() for s in evalCases.strip().splitlines()]
        for case in evalCases:
            self.assertEqual(valueForString(case), eval(case),
                'case=%r, valueForString()=%r, eval()=%r'
                % (case, valueForString(case), eval(case)))

        stringCases = [s.strip() for s in stringCases.strip().splitlines()]
        for case in stringCases:
            self.assertEqual(valueForString(case), case,
                'case=%r, valueForString()=%r'
                % (case, valueForString(case)))


if __name__ == '__main__':
    unittest.main()
