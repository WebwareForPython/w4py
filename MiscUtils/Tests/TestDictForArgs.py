import sys
import unittest

import FixPath
from MiscUtils.DictForArgs import *


class TestDictForArgs(unittest.TestCase):

    def testPositives(self):
#               print 'Positive cases:'
        tests = '''\
# Basics
x=1       == {'x': '1'}
x=1 y=2   == {'x': '1', 'y': '2'}

# Strings
x='a'     == {'x': 'a'}
x="a"     == {'x': 'a'}
x='a b'   == {'x': 'a b'}
x="a b"   == {'x': 'a b'}
x='a"'    == {'x': 'a"'}
x="a'"    == {'x': "a'"}
x="'a'"   == {'x': "'a'"}
x='"a"'   == {'x': '"a"'}

# No value
x         == {'x': '1'}
x y       == {'x': '1', 'y': '1'}
x y=2     == {'x': '1', 'y': '2'}
x=2 y     == {'x': '2', 'y': '1'}
'''
        tests = tests.splitlines()
        errCount = 0
        self._testPositive('', {})
        self._testPositive(' ', {})
        for test in tests:
            if '#' in test:
                test = test[:test.index('#')]
            test = test.strip()
            if test:
                input, output = test.split('==', 1)
                output = eval(output)
                result = DictForArgs(input)
                self._testPositive(input, output)

    def _testPositive(self, input, output):
        # print repr(input)
        # sys.stdout.flush()
        result = DictForArgs(input)
        self.assertEqual(result, output,
            'Expecting: %s\nGot: %s\n' % (repr(output), repr(result)))

    def testNegatives(self):
        # print 'Negative cases:'
        cases = '''\
-
$
!@#$
'x'=5
x=5 'y'=6
'''
        cases = cases.splitlines()
        errCount = 0
        for case in cases:
            if '#' in case:
                case = case[:case.index('#')]
            case = case.strip()
            if case:
                self._testNegative(case)

    def _testNegative(self, input):
        # print repr(input)
        # sys.stdout.flush()
        try:
            result = DictForArgs(input)
        except DictForArgsError:
            return  # success
        except Exception:
            self.fail('Expecting DictForArgError.\nGot: %s.\n' % sys.exc_info())
        else:
            self.fail('Expecting DictForArgError.\nGot: %s.\n' % repr(result))

    def testPyDictForArgs(self):
        cases = '''\
        x=1 == {'x': 1}
        x=1; y=2 == {'x': 1, 'y': 2}
        x='a' == {'x': 'a'}
        x="a"; y="""b""" == {'x': 'a', 'y': 'b'}
        x=(1, 2, 3) == {'x': (1, 2, 3)}
        x=['a', 'b'] == {'x': ['a', 'b']}
        x='a b'.split() == {'x': ['a', 'b']}
        x=['a b'.split(), 1]; y={'a': 1} == {'x': [['a', 'b'], 1], 'y': {'a': 1}}
'''.splitlines()
        for case in cases:
            case = case.strip()
            if case:
                source, answer = case.split('==', 1)
                answer = eval(answer)
                self.assertEqual(PyDictForArgs(source), answer)

    def testExpandDictWithExtras(self):
        d = {'Name': 'foo', 'Extras': 'x=1 y=2'}
        result = ExpandDictWithExtras(d)
        self.assertEqual(result, {'Name': 'foo', 'x': '1', 'y': '2'})
        d = {'Name': 'foo', 'bar': 'z = 3'}
        result = ExpandDictWithExtras(d)
        self.assertEqual(result, d)
        result = ExpandDictWithExtras(d, key='bar', delKey=False)
        self.assertEqual(result, {'Name': 'foo', 'bar': 'z = 3', 'z': '3'})


if __name__ == '__main__':
    unittest.main()
