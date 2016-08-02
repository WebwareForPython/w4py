import sys
import unittest

import FixPath
from MiscUtils.NamedValueAccess import (
    NamedValueAccessError, valueForKey, valueForName)
from MiscUtils import AbstractError, NoDefault


class T(object):
    pass


class T1(T):

    def foo(self):
        return 1


class T2(T):

    def _foo(self):
        return 1


class T3(T):

    def foo(self):
        return 1

    def _foo(self):
        return 0


class T4(T):

    def foo(self):
        return 1

    def __init__(self):
        self._foo = 0


class T5(T):

    def __init__(self):
        self.foo = 0

    def _foo(self):
        return 1


class T6(T):

    def __init__(self):
        self.foo = 1
        self._foo = 0


# Make a list of all the 'T' classes which are used in testing
tClasses = []
for name in dir():
    if name.startswith('T') and name[1:].isdigit():
        tClasses.append(globals()[name])


class NamedValueAccessTest(unittest.TestCase):
    """Abstract root ancestor for all test case classes in this file."""


class LookupTest(NamedValueAccessTest):
    """Abstract super class for the test cases covering the functions.

    Subclasses must implement self.lookup() and can make use of
    self.classes and self.objs.
    """

    def setUp(self):
        self.setUpClasses()
        self.setUpObjects()

    def setUpClasses(self):
        self.classes = tClasses

    def setUpObjects(self):
        self.objs = map(lambda klass: klass(), self.classes)

    def lookup(self, obj, key, default=NoDefault):
        raise AbstractError(self.__class__)

    def checkBasicAccess(self):
        """Check the basic access functionality.

        Invoke the look up function with key 'foo', expecting 1 in return.
        Invoke the look up with 'bar', expected an exception.
        Invoke the look up with 'bar' and default 2, expecting 2.
        """
        func = self.lookup
        for obj in self.objs:

            value = func(obj, 'foo')
            self.assertEqual(value, 1, 'value = %r, obj = %r' % (value, obj))

            self.assertRaises(NamedValueAccessError, func, obj, 'bar')

            value = func(obj, 'bar', 2)
            self.assertEqual(value, 2, 'value = %r, obj = %r' % (value, obj))

    def checkBasicAccessRepeated(self):
        """Just repeat checkBasicAccess multiple times to check stability."""
        for count in xrange(50):
            # Yes, it's safe to invoke this other particular test
            # multiple times without the usual setUp()/tearDown() cycle
            self.checkBasicAccess()


class ValueForKeyTest(LookupTest):

    def lookup(self, obj, key, default=NoDefault):
        return valueForKey(obj, key, default)


class ValueForNameTest(LookupTest):

    def lookup(self, obj, key, default=NoDefault):
        return valueForName(obj, key, default)

    def checkNamedValueAccess(self):
        objs = self.objs

        # link the objects
        for i in range(len(objs)-1):
            objs[i].nextObject = objs[i+1]

        # test the links
        for i in range(len(objs)):
            name = 'nextObject.' * i + 'foo'
            self.assertEqual(self.lookup(objs[0], name), 1)

    def checkDicts(self):
        d = {'origin': {'x': 1, 'y': 2},
            'size': {'width': 3, 'height': 4}}
        obj = self.objs[0]
        obj.rect = d

        self.assertEqual(self.lookup(d, 'origin.x'), 1)
        self.assertTrue(self.lookup(obj, 'rect.origin.x'))

        self.assertRaises(NamedValueAccessError, self.lookup, d, 'bar')
        self.assertRaises(NamedValueAccessError, self.lookup, obj,  'bar')

        self.assertEqual(self.lookup(d, 'bar', 2), 2)
        self.assertEqual(self.lookup(obj, 'rect.bar', 2), 2)


def makeTestSuite():
    testClasses = [ValueForKeyTest, ValueForNameTest]
    make = unittest.makeSuite
    suites = [make(klass, 'check') for klass in testClasses]
    return unittest.TestSuite(suites)


def testUse():
    runner = unittest.TextTestRunner(stream=sys.stdout)
    unittest.main(defaultTest='makeTestSuite', testRunner=runner)


def usage():
    sys.stdout = sys.stderr
    print 'usage:'
    print '  TestNamedValueAccess.py use'
    print '  TestNamedValueAccess.py leaks <iterations>'
    print
    sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        testUse()
    elif sys.argv[1] in ('-h', '--help', 'help'):
        usage()
    elif sys.argv[1] == 'use':
        testUse()
    elif sys.argv[1] == 'leaks':
        testLeaks()
    else:
        usage()
