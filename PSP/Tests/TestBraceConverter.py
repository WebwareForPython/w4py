"""Automated tests for the PSP BraceConverter

Contributed 2000-09-04 by Dave Wallace
"""

import sys
import unittest
from StringIO import StringIO

import FixPath
from PSP.BraceConverter import BraceConverter
from PSP.ServletWriter import ServletWriter


class DummyWriter(ServletWriter):
    """Dummy writer for testing."""

    def __init__(self):
        self._filehandle = StringIO()
        self._tabcnt = 3  # base indentation of our test examples
        self._blockcount = 0
        self._indentSpaces = ServletWriter._spaces
        self._useTabs = False
        self._useBraces = False
        self._indent = '    '
        self._userIndent = ServletWriter._emptyString

    def getOutput(self):
        return self._filehandle.getvalue()

    def close(self):
        self._filehandle.close()


class TestBraceConverter(unittest.TestCase):

    def trim(self, text):
        return '\n'.join(filter(None, map(str.rstrip, text.splitlines())))

    def assertParses(self, input, expected):
        dummyWriter = DummyWriter()
        braceConverter = BraceConverter()
        for line in input.splitlines():
            braceConverter.parseLine(line, dummyWriter)
        output = dummyWriter.getOutput()
        dummyWriter.close()
        output, expected = map(self.trim, (output, expected))
        self.assertEqual(output, expected,
            '\n\nOutput:\n%s\n\nExpected:\n%s\n' % (output, expected))

    def testSimple(self):
        self.assertParses('''
            if a == b: { return True } else: { return False }
        ''', '''
            if a == b:
                return True
            else:
                return False
        ''')

    def testDict(self):
        self.assertParses('''
            for x in range(10): { q = {
            'test': x
            }
            print x
            }
        ''', '''
            for x in range(10):
                q = {
                'test': x
                }
                print x
        ''')

    def testNestedDict(self):
        self.assertParses(r'''
            if x: { q = {'test': x}; print x} else: { print "\"done\"" #""}{
            x = { 'test1': {'sub2': {'subsub1': 2}} # yee ha
            }
            } print "all done"
        ''', r'''
            if x:
                q = {'test': x}; print x
            else:
                print "\"done\"" #""}{
                x = { 'test1': {'sub2': {'subsub1': 2}} # yee ha
                }
            print "all done"
        ''')


if __name__ == '__main__':
    unittest.main()
