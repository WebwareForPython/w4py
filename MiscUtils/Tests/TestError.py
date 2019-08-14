import unittest

import FixPath
from MiscUtils.Error import Error


class DummyObject:

    def __repr__(self):
        return '<dummy>'


class TestError(unittest.TestCase):

    def testNone(self):
        err = Error(None, None)
        self.assertEqual('ERROR: None', str(err))
        self.assertEqual('ERROR(object=None; message=None; data={})', repr(err))
        self.assertTrue(err.object() is None)
        self.assertTrue(err.message() is None)

    def testObjMessage(self):
        obj = DummyObject()
        err = Error(obj, 'test')
        self.assertEqual('ERROR: test', str(err))
        # Should produce something like:
        # "ERROR(object=<function test at 0x74f70>; message='test'; data={})"
        self.assertTrue(repr(err).endswith("; message='test'; data={})"))
        self.assertTrue(err.object() is obj)
        self.assertTrue(err.message() == 'test')

    def testValueDict(self):
        err = Error(None, '', a=5, b='.')
        self.assertEqual('ERROR: ', str(err))
        self.assertEqual("ERROR(object=None; message=''; data={'a': 5, 'b': '.'})",
            repr(err).replace("{'b': '.', 'a': 5}", "{'a': 5, 'b': '.'}"))
        self.assertTrue(err.keys() in [['a', 'b'], ['b', 'a']])
        self.assertTrue(isinstance(err['a'], int))
        self.assertTrue(isinstance(err['b'], str))

    def testVarArgs(self):
        err = Error(None, '', {'a': 5}, b='.')
        self.assertEqual('ERROR: ', str(err))
        self.assertEqual("ERROR(object=None; message=''; data={'a': 5, 'b': '.'})",
            repr(err).replace("{'b': '.', 'a': 5}", "{'a': 5, 'b': '.'}"))
        self.assertTrue(err.keys() in [['a', 'b'], ['b', 'a']])
        self.assertTrue(isinstance(err['a'], int))
        self.assertTrue(isinstance(err['b'], str))


if __name__ == '__main__':
    unittest.main()
