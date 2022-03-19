#!/usr/bin/env python2

import os
import sys
import unittest
from StringIO import StringIO

sys.path.insert(1, os.path.abspath('../..'))

from WebUtils.FieldStorage import FieldStorage


class TestFieldStorage(unittest.TestCase):

    def testGetRequest(self):
        fs = FieldStorage(environ=dict(
            REQUEST_METHOD='GET', QUERY_STRING='a=1&b=2&b=3&c=3'))
        self.assertEqual(fs.getfirst('a'), '1')
        self.assertEqual(fs.getfirst('b'), '2')
        self.assertEqual(fs.getfirst('c'), '3')
        self.assertEqual(fs.getlist('a'), ['1'])
        self.assertEqual(fs.getlist('b'), ['2', '3'])
        self.assertEqual(fs.getlist('c'), ['3'])

    def testPostRequestWithQuery(self):
        fs = FieldStorage(fp=StringIO(), environ=dict(
            REQUEST_METHOD='POST', QUERY_STRING='a=1&b=2&b=3&c=3'))
        self.assertEqual(fs.getfirst('a'), '1')
        self.assertEqual(fs.getfirst('b'), '2')
        self.assertEqual(fs.getfirst('c'), '3')
        self.assertEqual(fs.getlist('a'), ['1'])
        self.assertEqual(fs.getlist('b'), ['2', '3'])
        self.assertEqual(fs.getlist('c'), ['3'])

    def testPostRequestWithBody(self):
        fs = FieldStorage(
            fp=StringIO('d=4&e=5&e=6&f=6'), environ=dict(
            REQUEST_METHOD='POST'))
        self.assertEqual(fs.getfirst('d'), '4')
        self.assertEqual(fs.getfirst('e'), '5')
        self.assertEqual(fs.getfirst('f'), '6')
        self.assertEqual(fs.getlist('d'), ['4'])
        self.assertEqual(fs.getlist('e'), ['5', '6'])
        self.assertEqual(fs.getlist('f'), ['6'])

    def testPostRequestOverrides(self):
        fs = FieldStorage(
            fp=StringIO('b=8&c=9&d=4&e=5&e=6&f=6'), environ=dict(
            REQUEST_METHOD='POST', QUERY_STRING='a=1&b=2&b=3&c=3'))
        self.assertEqual(fs.getfirst('a'), '1')
        self.assertEqual(fs.getfirst('b'), '8')
        self.assertEqual(fs.getfirst('c'), '9')
        self.assertEqual(fs.getfirst('d'), '4')
        self.assertEqual(fs.getfirst('e'), '5')
        self.assertEqual(fs.getfirst('f'), '6')
        self.assertEqual(fs.getlist('a'), ['1'])
        self.assertEqual(fs.getlist('b'), ['8'])
        self.assertEqual(fs.getlist('c'), ['9'])
        self.assertEqual(fs.getlist('d'), ['4'])
        self.assertEqual(fs.getlist('e'), ['5', '6'])
        self.assertEqual(fs.getlist('f'), ['6'])

    def testPostRequestWithTooManyFields(self):
        if sys.version_info < (2, 7, 16):
            return  # this feature is only supported in Python >= 2.7.16
        fs = FieldStorage(fp=StringIO(), environ=dict(
            REQUEST_METHOD='POST', QUERY_STRING='a=1&a=2&a=3&a=4'),
            max_num_fields=4)
        self.assertEqual(fs.getlist('a'), ['1', '2', '3', '4'])
        if hasattr(fs, 'max_num_fields'):  # only test if this is supported
            self.assertRaises(
                ValueError, FieldStorage,
                fp=StringIO(), environ=dict(
                    REQUEST_METHOD='POST', QUERY_STRING='a=1&a=2&a=3&a=4'),
                max_num_fields=3)

    def testPostRequestWithQueryWithSemicolon1(self):
        fs = FieldStorage(fp=StringIO(), environ=dict(
            REQUEST_METHOD='POST', QUERY_STRING='a=1&b=2;b=3&c=3'))
        self.assertEqual(fs.getfirst('a'), '1')
        self.assertEqual(fs.getfirst('c'), '3')
        self.assertEqual(fs.getlist('a'), ['1'])
        self.assertEqual(fs.getlist('c'), ['3'])
        separator = getattr(fs, 'separator', None)
        if separator:  # patched Python version, splits only &
            self.assertEqual(fs.getfirst('b'), '2;b=3')
            self.assertEqual(fs.getlist('b'), ['2;b=3'])
            fs = FieldStorage(fp=StringIO(), environ=dict(
                REQUEST_METHOD='POST', QUERY_STRING='a=1&b=2&b=3&c=3'),
                separator='&')
            self.assertEqual(fs.getfirst('a'), '1')
            self.assertEqual(fs.getfirst('b'), '2')
            self.assertEqual(fs.getfirst('c'), '3')
            self.assertEqual(fs.getlist('a'), ['1'])
            self.assertEqual(fs.getlist('b'), ['2', '3'])
            self.assertEqual(fs.getlist('c'), ['3'])
        else:  # old Python version, splits ; and &
            self.assertEqual(fs.getfirst('b'), '2')
            self.assertEqual(fs.getlist('b'), ['2', '3'])

    def testPostRequestWithQueryWithSemicolon2(self):
        fs = FieldStorage(fp=StringIO(), environ=dict(
            REQUEST_METHOD='POST', QUERY_STRING='a=1;b=2&b=3;c=3'))
        separator = getattr(fs, 'separator', None)
        if separator:  # new Python version, splits only &
            self.assertEqual(fs.getfirst('a'), '1;b=2')
            self.assertEqual(fs.getfirst('b'), '3;c=3')
            self.assertIsNone(fs.getfirst('c'))
            self.assertEqual(fs.getlist('a'), ['1;b=2'])
            self.assertEqual(fs.getlist('b'), ['3;c=3'])
            self.assertEqual(fs.getlist('c'), [])
            fs = FieldStorage(fp=StringIO(), environ=dict(
                REQUEST_METHOD='POST', QUERY_STRING='a=1;b=2;b=3;c=3'),
                separator=';')
            self.assertEqual(fs.getfirst('a'), '1')
            self.assertEqual(fs.getfirst('b'), '2')
            self.assertEqual(fs.getfirst('c'), '3')
            self.assertEqual(fs.getlist('a'), ['1'])
            self.assertEqual(fs.getlist('b'), ['2', '3'])
            self.assertEqual(fs.getlist('c'), ['3'])
        else:  # old Python version, splits ; and &
            self.assertEqual(fs.getfirst('a'), '1')
            self.assertEqual(fs.getfirst('b'), '2')
            self.assertEqual(fs.getfirst('c'), '3')
            self.assertEqual(fs.getlist('a'), ['1'])
            self.assertEqual(fs.getlist('b'), ['2', '3'])
            self.assertEqual(fs.getlist('c'), ['3'])


if __name__ == '__main__':
    unittest.main()
