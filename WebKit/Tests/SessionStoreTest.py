import os
import sys
import unittest
from time import time

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from MiscUtils import StringIO
from WebKit.SessionStore import SessionStore
from WebKit.SessionMemoryStore import SessionMemoryStore
from WebKit.SessionFileStore import SessionFileStore
from WebKit.SessionDynamicStore import SessionDynamicStore
from WebKit.SessionShelveStore import SessionShelveStore
from WebKit.SessionMemcachedStore import SessionMemcachedStore
from WebKit.SessionRedisStore import SessionRedisStore


class Application(object):
    """Mock application."""

    _sessionDir = 'SessionStoreTestDir'
    _alwaysSaveSessions = True

    def setting(self, key, default=None):
        return dict(
            DynamicSessionTimeout=1,
            MaxDynamicMemorySessions=3,
            MemcachedOnIteration=None,
        ).get(key, default)

    def handleException(self):
        raise Exception('Application Error')


class Session(object):
    """Mock session."""

    _last_expired = None

    def __init__(self, identifier=7, value=None):
        self._identifier = 'foo-%d' % identifier
        self._data = dict(bar=value or identifier * 6)
        self._expired = self._dirty = False
        self._timeout = 1800
        self._lastAccessTime = time() - identifier * 400
        self._isNew = True

    def identifier(self):
        return self._identifier

    def expiring(self):
        self._expired = True
        Session._last_expired = self._identifier

    def isDirty(self):
        return self._dirty

    def setDirty(self, dirty=True):
        self._dirty = dirty

    def isExpired(self):
        return self._expired

    def timeout(self):
        return self._timeout

    def data(self):
        return self._data

    def bar(self):
        return self._data.get('bar')

    def setBar(self, value):
        self._isNew = False
        self._data['bar'] = value

    def isNew(self):
        return self._isNew

    def lastAccessTime(self):
        return self._lastAccessTime


class SessionStoreTest(unittest.TestCase):

    _storeclass = SessionStore

    _app = Application()

    def setUp(self):
        Session._last_expired = None
        self._store = self._storeclass(self._app)

    def testApplication(self):
        self.assertEqual(self._store.application(), self._app)

    def testEncodeDecode(self):
        session = Session()
        s = StringIO()
        self._store.encoder()(session, s)
        output = s.getvalue()
        s.close()
        self.assertTrue(isinstance(output, str))
        s = StringIO(output)
        output = self._store.decoder()(s)
        s.close()
        self.assertTrue(type(output) is type(session))
        self.assertEqual(output._data, session._data)

    def testSetEncoderDecoder(self):
        encoder = lambda obj, f: f.write(str(obj))
        decoder = lambda f: eval(f.read())
        self._store.setEncoderDecoder(encoder, decoder)
        self.assertEqual(self._store.encoder(), encoder)
        self.assertEqual(self._store.decoder(), decoder)


class SessionMemoryStoreTest(SessionStoreTest):

    _storeclass = SessionMemoryStore

    def setUp(self):
        d = self._app._sessionDir
        if not os.path.exists(d):
            os.mkdir(d)
        SessionStoreTest.setUp(self)
        self._store.clear()
        for n in range(7):
            session = Session(n)
            self._store[session.identifier()] = session
            self.assertFalse(session.isExpired())

    def tearDown(self):
        self._store.clear()
        self._store.storeAllSessions()
        d = self._app._sessionDir
        for filename in os.listdir(d):
            os.remove(os.path.join(d, filename))
        os.rmdir(d)
        SessionStoreTest.tearDown(self)

    def testLen(self):
        self.assertEqual(len(self._store), 7)

    def testGetItem(self):
        store = self._store
        self.assertEqual(self._store['foo-3'].bar(), 18)
        self.assertRaises(KeyError, store.__getitem__, 'foo-7')

    def testSetItem(self):
        session = Session()
        key = session.identifier()
        self._store[key] = session
        self.assertEqual(self._store[key].data(), session.data())

    def testDelItem(self):
        del self._store['foo-3']
        self.assertFalse('foo-3' in self._store)
        self.assertEqual(Session._last_expired, 'foo-3')
        try:
            self._store['foo-3']
        except KeyError:
            pass
        self.assertRaises(KeyError, self._store.__delitem__, 'foo-3')

    def testContains(self):
        store = self._store
        self.assertTrue('foo-0' in store
            and 'foo-3' in store and 'foo-6' in store)
        self.assertFalse('foo' in store)
        self.assertFalse('0' in store or '3' in store or '6' in store)
        self.assertFalse('foo-7' in store)

    def testIter(self):
        keys = set()
        for key in self._store:
            keys.add(key)
        self.assertEqual(keys, set('foo-%d' % n  for n in range(7)))

    def testKeys(self):
        keys = self._store.keys()
        self.assertTrue(isinstance(keys, list))
        self.assertEqual(set(keys), set('foo-%d' % n  for n in range(7)))

    def testClear(self):
        store = self._store
        store.clear()
        self.assertFalse('foo-0' in store
            or 'foo-3' in store or 'foo-6' in store)

    def testSetDefault(self):
        store = self._store
        session = Session()
        self.assertEqual(store.setdefault('foo-3').bar(), 18)
        self.assertEqual(store.setdefault('foo-3', session).bar(), 18)
        self.assertEqual(store.setdefault('foo-7', session).bar(), 42)
        self.assertEqual(store.setdefault('foo-7').bar(), 42)

    def testPop(self):
        store = self._store
        session = self._store['foo-3']
        self.assertFalse(session.isExpired())
        self.assertEqual(store.pop('foo-3').bar(), 18)
        self.assertRaises(KeyError, store.pop, 'foo-3')
        self.assertEqual(store.pop('foo-3', Session()).bar(), 42)
        self.assertRaises(KeyError, store.pop, 'foo-3')
        self.assertFalse(session.isExpired())

    def testGet(self):
        self.assertEqual(self._store.get('foo-4').bar(), 24)
        self.assertEqual(self._store.get('foo-4', Session()).bar(), 24)
        self.assertEqual(self._store.get('foo-7'), None)
        self.assertEqual(self._store.get('foo-7', Session()).bar(), 42)

    def testStoreSession(self):
        session = self._store['foo-3']
        self.assertEqual(session.bar(), 18)
        session.setBar(19)
        self.assertEqual(session.bar(), 19)
        self._store.storeSession(session)
        session = self._store['foo-3']
        self.assertEqual(session.bar(), 19)
        session = Session(3, 20)
        self._store.storeSession(session)
        session = self._store['foo-3']
        self.assertEqual(session.bar(), 20)
        session = Session()
        self._store.storeSession(session)
        session = self._store['foo-7']
        self.assertEqual(session.bar(), 42)

    def testItems(self):
        items = self._store.items()
        self.assertTrue(isinstance(items, list))
        self.assertEqual(len(items), 7)
        self.assertTrue(isinstance(items[4], tuple))
        self.assertEqual(len(items[4]), 2)
        self.assertEqual(dict(items)['foo-3'].bar(), 18)

    def testIterItems(self):
        items = self._store.iteritems()
        self.assertFalse(isinstance(items, list))
        items = list(items)
        self.assertTrue(isinstance(items[4], tuple))
        self.assertEqual(len(items[4]), 2)
        self.assertEqual(dict(items)['foo-3'].bar(), 18)

    def testValues(self):
        values = self._store.values()
        self.assertTrue(isinstance(values, list))
        self.assertEqual(len(values), 7)
        value = values[4]
        self.assertTrue(isinstance(value, Session))
        self.assertEqual(self._store[value.identifier()].bar(), value.bar())

    def testIterValues(self):
        values = self._store.itervalues()
        self.assertFalse(isinstance(values, list))
        values = list(values)
        self.assertEqual(len(values), 7)
        value = values[4]
        self.assertTrue(isinstance(value, Session))
        self.assertEqual(self._store[value.identifier()].bar(), value.bar())

    def testCleanStaleSessions(self):
        store = self._store
        self.assertEqual(len(store), 7)
        self.assertTrue('foo-0' in store and 'foo-4' in store)
        self.assertTrue('foo-5' in store and 'foo-6' in store)
        store.cleanStaleSessions()
        self.assertEqual(len(store), 5)
        self.assertTrue('foo-0' in store and 'foo-4' in store)
        self.assertFalse('foo-5' in store or 'foo-6' in store)


class SessionFileStoreTest(SessionMemoryStoreTest):

    _storeclass = SessionFileStore

    def testMemoryStoreRestoreFiles(self):
        app = self._app
        store = SessionMemoryStore(app)
        self.assertEqual(len(store), 7)
        self.assertTrue('foo-0' in store and 'foo-6' in store)
        store = SessionMemoryStore(app, restoreFiles=False)
        self.assertEqual(len(store), 0)
        self.assertFalse('foo-0' in store or 'foo-6' in store)

    def testFileStoreRestoreFiles(self):
        app = self._app
        store = SessionFileStore(app)
        self.assertEqual(len(store), 7)
        self.assertTrue('foo-0' in store and 'foo-6' in store)
        store = SessionFileStore(app, restoreFiles=False)
        self.assertEqual(len(store), 0)
        self.assertFalse('foo-0' in store or 'foo-6' in store)


class SessionDynamicStoreTest(SessionMemoryStoreTest):

    _storeclass = SessionDynamicStore

    def testCleanStaleSessions(self):
        store = self._store
        memoryStore = store._memoryStore
        fileStore = store._fileStore
        self.assertEqual(len(memoryStore), 7)
        self.assertEqual(len(fileStore), 0)
        SessionMemoryStoreTest.testCleanStaleSessions(self)
        self.assertEqual(len(memoryStore), 3)
        self.assertEqual(len(fileStore), 2)
        self.assertTrue('foo-0' in memoryStore and 'foo-2' in memoryStore)
        self.assertTrue('foo-3' in fileStore and 'foo-4' in fileStore)


class SessionShelveStoreTest(SessionMemoryStoreTest):

    _storeclass = SessionShelveStore

    def testFileShelveRestoreFiles(self):
        app = self._app
        self._store.intervalSweep()
        store = SessionShelveStore(app)
        self.assertEqual(len(store), 7)
        session = store['foo-3']
        self.assertTrue('foo-0' in store and 'foo-6' in store)
        store = SessionShelveStore(app,
            restoreFiles=False, filename='Session.Store2')
        self.assertEqual(len(store), 0)
        self.assertFalse('foo-0' in store or 'foo-6' in store)
        store['foo-3'] = session
        store.storeAllSessions()
        store = SessionShelveStore(app, filename='Session.Store2')
        self.assertEqual(len(store), 1)
        self.assertTrue('foo-3' in store)
        self.assertFalse('foo-0' in store or 'foo-6' in store)


class SessionMemcachedStoreTest(SessionMemoryStoreTest):

    _storeclass = SessionMemcachedStore

    def setUp(self):
        SessionMemoryStoreTest.setUp(self)
        self.setOnIteration()

    def tearDown(self):
        self.setOnIteration()
        SessionMemoryStoreTest.tearDown(self)

    def setOnIteration(self, onIteration=None):
        self._store._onIteration = onIteration

    def testLen(self):
        self.assertEqual(len(self._store), 0)
        self.setOnIteration('Error')
        self.assertRaises(NotImplementedError, len, self._store)

    def testIter(self):
        keys = [key for key in self._store]
        self.assertEqual(keys, [])
        self.setOnIteration('Error')
        keys = lambda: [key for key in self._store]
        self.assertRaises(NotImplementedError, keys)

    def testKeys(self):
        keys = self._store.keys()
        self.assertEqual(keys, [])
        self.setOnIteration('Error')
        self.assertRaises(NotImplementedError, self._store.keys)

    def testItems(self):
        items = self._store.items()
        self.assertEqual(items, [])
        self.setOnIteration('Error')
        self.assertRaises(NotImplementedError, self._store.items)

    def testIterItems(self):
        items = [key for key in self._store.iteritems()]
        self.assertEqual(items, [])
        self.setOnIteration('Error')
        items = lambda:  [key for key in self._store.iteritems()]
        self.assertRaises(NotImplementedError, items)

    def testValues(self):
        values = self._store.values()
        self.assertEqual(values, [])
        self.setOnIteration('Error')
        self.assertRaises(NotImplementedError, self._store.values)

    def testIterValues(self):
        values = [key for key in self._store.itervalues()]
        self.assertEqual(values, [])
        self.setOnIteration('Error')
        values = lambda:  [key for key in self._store.values()]
        self.assertRaises(NotImplementedError, values)

    def testClear(self):
        self._store.clear()
        self.setOnIteration('Error')
        self.assertRaises(NotImplementedError, self._store.clear)

    def testCleanStaleSessions(self):
        self._store.cleanStaleSessions()


class SessionRedisStoreTest(SessionMemoryStoreTest):

    _storeclass = SessionRedisStore

    def setUp(self):
        SessionMemoryStoreTest.setUp(self)

    def tearDown(self):
        SessionMemoryStoreTest.tearDown(self)

    def testCleanStaleSessions(self):
        self._store.cleanStaleSessions()
