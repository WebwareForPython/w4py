"""This module tests UserManagers in different permutations.

UserManagers can save their data to files, or to a MiddleKit database.
For MiddleKit, the database can be MySQL, PostgreSQL, MSSQL or SQLite,
but we test only with the SQLite database.
"""

import os
import sys
import logging
import unittest
import shutil

_log = logging.getLogger(__name__)

testDir = os.path.dirname(os.path.abspath(__file__))
webwarePath = os.path.dirname(os.path.dirname(testDir))
if sys.path[0] != webwarePath:
    sys.path.insert(0, webwarePath)


class UserManagerTest(unittest.TestCase):
    """Tests for the base UserManager class."""

    def setUp(self):
        from UserKit.UserManager import UserManager
        self._mgr = UserManager()

    def checkSettings(self):
        mgr = self._mgr
        value = 5.1
        mgr.setModifiedUserTimeout(value)
        self.assertEqual(mgr.modifiedUserTimeout(), value)
        mgr.setCachedUserTimeout(value)
        self.assertEqual(mgr.cachedUserTimeout(), value)
        mgr.setActiveUserTimeout(value)
        self.assertEqual(mgr.activeUserTimeout(), value)

    def checkUserClass(self):
        mgr = self._mgr
        from UserKit.User import User
        class SubUser(User):
            pass
        mgr.setUserClass(SubUser)
        self.assertEqual(mgr.userClass(), SubUser,
            "We should be able to set a custom user class.")
        class Poser(object):
            pass
        self.assertRaises(Exception, mgr.setUserClass, Poser), (
            "Setting a customer user class that doesn't extend UserKit.User"
            " should fail.")

    def tearDown(self):
        self._mgr.shutDown()
        self._mgr = None


class _UserManagerToSomewhereTest(UserManagerTest):
    """Common tests for all UserManager subclasses.

    This abstract class provides some tests that all user managers should pass.
    Subclasses are responsible for overriding setUp() and tearDown() for which
    they should invoke super.
    """

    def setUp(self):
        pass  # nothing for no

    def tearDown(self):
        self._mgr = None

    def testBasics(self):
        mgr = self._mgr
        user = self._user = mgr.createUser('foo', 'bar')
        self.assertEqual(user.manager(), mgr)
        self.assertEqual(user.name(), 'foo')
        self.assertEqual(user.password(), 'bar')
        self.assertFalse(user.isActive())
        self.assertEqual(mgr.userForSerialNum(user.serialNum()), user)
        self.assertEqual(mgr.userForExternalId(user.externalId()), user)
        self.assertEqual(mgr.userForName(user.name()), user)
        externalId = user.externalId()  # for use later in testing

        users = mgr.users()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0], user,
            'users[0]=%r, user=%r' % (users[0], user))
        self.assertEqual(len(mgr.activeUsers()), 0)
        self.assertEqual(len(mgr.inactiveUsers()), 1)

        # login
        user2 = mgr.login(user, 'bar')
        self.assertEqual(user, user2)
        self.assertTrue(user.isActive())
        self.assertEqual(len(mgr.activeUsers()), 1)
        self.assertEqual(len(mgr.inactiveUsers()), 0)

        # logout
        user.logout()
        self.assertFalse(user.isActive())
        self.assertEqual(mgr.numActiveUsers(), 0)

        # login via user
        result = user.login('bar')
        self.assertEqual(result, user)
        self.assertTrue(user.isActive())
        self.assertEqual(mgr.numActiveUsers(), 1)

        # logout via user
        user.logout()
        self.assertFalse(user.isActive())
        self.assertEqual(mgr.numActiveUsers(), 0)

        # login a 2nd time, but with bad password
        user.login('bar')
        user.login('rab')
        self.assertFalse(user.isActive())
        self.assertEqual(mgr.numActiveUsers(), 0)

        # Check that we can access the user when he is not cached
        mgr.clearCache()
        user = mgr.userForSerialNum(1)
        self.assertTrue(user)
        self.assertEqual(user.password(), 'bar')

        mgr.clearCache()
        user = self._mgr.userForExternalId(externalId)
        self.assertTrue(user)
        self.assertEqual(user.password(), 'bar')

        mgr.clearCache()
        user = self._mgr.userForName('foo')
        self.assertTrue(user)
        self.assertEqual(user.password(), 'bar')

    def testUserAccess(self):
        mgr = self._mgr
        user = mgr.createUser('foo', 'bar')

        self.assertEqual(mgr.userForSerialNum(user.serialNum()), user)
        self.assertEqual(mgr.userForExternalId(user.externalId()), user)
        self.assertEqual(mgr.userForName(user.name()), user)

        self.assertRaises(KeyError, mgr.userForSerialNum, 1000)
        self.assertRaises(KeyError, mgr.userForExternalId, 'asdf')
        self.assertRaises(KeyError, mgr.userForName, 'asdf')

        self.assertEqual(mgr.userForSerialNum(1000, 1), 1)
        self.assertEqual(mgr.userForExternalId('asdf', 1), 1)
        self.assertEqual(mgr.userForName('asdf', 1), 1)

    def testDuplicateUser(self):
        mgr = self._mgr
        user = self._user = mgr.createUser('foo', 'bar')
        self.assertEqual(user.name(), 'foo')
        self.assertRaises(KeyError, mgr.createUser, 'foo', 'bar')
        userClass = mgr.userClass()
        self.assertRaises(KeyError, userClass, mgr, 'foo', 'bar')


class UserManagerToFileTest(_UserManagerToSomewhereTest):
    """Tests for the UserManagerToFile class."""

    def setUp(self):
        _UserManagerToSomewhereTest.setUp(self)
        from UserKit.UserManagerToFile import UserManagerToFile
        self._mgr = UserManagerToFile()
        self.setUpUserDir(self._mgr)

    def setUpUserDir(self, mgr):
        path = 'Users'
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
        os.mkdir(path)
        mgr.setUserDir(path)

    def tearDown(self):
        path = 'Users'
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
        _UserManagerToSomewhereTest.tearDown(self)


class UserManagerToMiddleKitTest(_UserManagerToSomewhereTest):
    """Tests for the UserManagerToMiddleKit class."""

    def write(self, text):
        self._output.append(text)

    def setUp(self):
        _UserManagerToSomewhereTest.setUp(self)
        self._mgr = self._store = None

        self._output = []
        self._stdout, self._stderr = sys.stdout, sys.stderr
        sys.stdout = sys.stderr = self
        try:
            # Generate Python and SQL from our test MiddleKit Model
            from MiddleKit.Design.Generate import Generate

            generator = Generate()
            modelFileName = os.path.join(testDir, 'UserManagerTest.mkmodel')

            # We test only with SQLite for ease of setup
            generationDir = os.path.join(testDir, 'mk_SQLite')
            args = 'Generate.py --db SQLite --model %s --outdir %s' % (
                modelFileName, generationDir)
            Generate().main(args.split())
            createScript = os.path.join(generationDir, 'GeneratedSQL', 'Create.sql')

            self.assertTrue(os.path.exists(createScript),
                'The generation process should create some SQL files.')
            self.assertTrue(os.path.exists(os.path.join(generationDir,
                'UserForMKTest.py')), 'The generation process'
                    ' should create some Python files.')

            from MiddleKit.Run.SQLiteObjectStore import SQLiteObjectStore

            # Create store and connect to database
            databaseFile = os.path.join(generationDir, 'test.db')
            self._store = SQLiteObjectStore(database=databaseFile)
            self._store.executeSQLScript(open(createScript).read())
            self._store.readModelFileNamed(modelFileName)

            from MiddleKit.Run.MiddleObject import MiddleObject
            from UserKit.UserManagerToMiddleKit import UserManagerToMiddleKit
            from UserKit.Tests.mk_SQLite.UserForMKTest import UserForMKTest
            self.assertTrue(issubclass(UserForMKTest, MiddleObject))
            from UserKit.User import User
            if not issubclass(UserForMKTest, User):
                UserForMKTest.__bases__ += (User,)
                self.assertTrue(issubclass(UserForMKTest, (MiddleObject, User)))

            def __init__(self, manager, name, password):
                base1 = self.__class__.__bases__[0]
                base2 = self.__class__.__bases__[1]
                base1.__init__(self)
                base2.__init__(self,
                    manager=manager, name=name, password=password)

            UserForMKTest.__init__ = __init__
            self._mgr = self.userManagerClass()(
                userClass=UserForMKTest, store=self._store)

        except Exception:
            sys.stdout, sys.stderr = self._stdout, self._stderr
            print "Error in %s.SetUp." % self.__class__.__name__
            print ''.join(self._output)
            raise
        else:
            sys.stdout, sys.stderr = self._stdout, self._stderr

    def testUserClass(self):
        pass

    def userManagerClass(self):
        from UserKit.UserManagerToMiddleKit import UserManagerToMiddleKit
        return UserManagerToMiddleKit

    def tearDown(self):
        self._output = []
        self._stdout, self._stderr = sys.stdout, sys.stderr
        sys.stdout = sys.stderr = self
        try:
            # close user manager and object store
            if self._mgr:
                self._mgr.shutDown()
                self._mgr = None
            if self._store:
                self._store.discardEverything()
                if self._store._connected:
                    self._store._connection.close()
                self._store = None
            # clean out generated files
            path = os.path.join(testDir, 'mk_SQLite')
            if os.path.exists(path):
                shutil.rmtree(path, ignore_errors=True)
        except Exception:
            sys.stdout, sys.stderr = self._stdout, self._stderr
            print "Error in %s.SetUp." % self.__class__.__name__
            print ''.join(self._output)
            raise
        else:
            sys.stdout, sys.stderr = self._stdout, self._stderr

        _UserManagerToSomewhereTest.tearDown(self)


class RoleUserManagerToFileTest(UserManagerToFileTest):
    """Tests for the RoleUserManagerToFile class."""

    def setUp(self):
        UserManagerToFileTest.setUp(self)
        from UserKit.RoleUserManagerToFile import RoleUserManagerToFile as umClass
        self._mgr = umClass()
        self.setUpUserDir(self._mgr)


class RoleUserManagerToMiddleKitTest(UserManagerToMiddleKitTest):
    """Tests for the RoleUserManagerToMiddleKit class."""

    def userManagerClass(self):
        from UserKit.RoleUserManagerToMiddleKit import RoleUserManagerToMiddleKit
        return RoleUserManagerToMiddleKit


def makeTestSuite():
    testClasses = [
        UserManagerTest, UserManagerToFileTest, RoleUserManagerToFileTest,
        UserManagerToMiddleKitTest, RoleUserManagerToMiddleKitTest]
    tests = [unittest.makeSuite(klass) for klass in testClasses]
    return unittest.TestSuite(tests)


def main():
    suite = makeTestSuite()
    runner = unittest.TextTestRunner()
    runner.run(suite)


if __name__ == '__main__':
    main()
