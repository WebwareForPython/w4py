#!/usr/bin/env python

"""AllTests.py - This module runs the automated tests in all the components.

To run specific test cases, pass one or more names of package/module names
on the command line which contain the test cases to be run.

Usage:
    python AllTests.py                  - Runs all the unittests
    python AllTests.py mypackage.MyFile - Runs the tests in 'mypackage/MyFile'
"""


alltestnames = [

    'WebUtils.Tests.TestFuncs',
    'WebUtils.Tests.TestFieldStorage',
    'WebUtils.Tests.TestHTMLTag.makeTestSuite',

    'MiscUtils.Tests.TestCSVParser',
    'MiscUtils.Tests.TestNamedValueAccess.makeTestSuite',
    'MiscUtils.Tests.TestError',
    'MiscUtils.Tests.TestFuncs',
    'MiscUtils.Tests.TestPickleCache',
    'MiscUtils.Tests.TestDataTable',
    'MiscUtils.Tests.TestDateInterval',
    'MiscUtils.Tests.TestDateParser',
    'MiscUtils.Tests.TestDictForArgs',

    'WebKit.Tests.SessionStoreTest',
    'WebKit.Tests.Basic.Test',

    'TaskKit.Tests.Test.makeTestSuite',

    'PSP.Tests.TestContext',
    'PSP.Tests.TestUtils',
    'PSP.Tests.TestBraceConverter',
    'PSP.Tests.TestCompiler',

    'UserKit.Tests.ExampleTest',
    'UserKit.Tests.RoleTest',
    'UserKit.Tests.UserManagerTest.makeTestSuite',

]

import site
import sys
import unittest
import logging


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig()  # default level is WARN
    print
    print
    # If no arguments are given, all of the test cases are run.
    if len(sys.argv) == 1:
        testnames = alltestnames
        verbosity = 2
        logging.getLogger().setLevel(logging.INFO)
        print 'Loading all Webware Tests...'
    else:
        testnames = sys.argv[1:]
        # Turn up verbosity and logging level
        verbosity = 3
        logging.getLogger().setLevel(logging.DEBUG)
        print 'Loading tests %s...' % testnames

    tests = unittest.TestSuite()

    # We could just use defaultTestLoader.loadTestsFromNames(),
    # but it doesn't give a good error message when it cannot load a test.
    # So we load all tests individually and raise appropriate exceptions.
    for test in testnames:
        try:
            tests.addTest(unittest.defaultTestLoader.loadTestsFromName(test))
        except Exception:
            print 'ERROR: Skipping tests from "%s".' % test
            try:  # just try to import the test after loading failed
                __import__(test)
            except ImportError:
                print 'Could not import the test module.'
            else:
                print 'Could not load the test suite.'
            from traceback import print_exc
            print_exc()

    print
    print 'Running the tests...'
    unittest.TextTestRunner(verbosity=verbosity).run(tests)
