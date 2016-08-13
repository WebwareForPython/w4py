"""Tests various functions of Users and Roles by running example code."""

import os
import sys
import shutil
import unittest

testDir = os.path.dirname(os.path.abspath(__file__))
webwarePath = os.path.dirname(os.path.dirname(testDir))
if sys.path[0] != webwarePath:
    sys.path.insert(0, webwarePath)


class SimpleExampleTest(unittest.TestCase):
    """A simple example to illustrate how to use UserKit."""

    def setUpDataDir(self, userManager):
        """Make a folder for UserManager data."""

        self._userDataDir = os.path.join(testDir, 'Users')

        if os.path.exists(self._userDataDir):
            shutil.rmtree(self._userDataDir, ignore_errors=True)
        os.mkdir(self._userDataDir)

        userManager.setUserDir(self._userDataDir)

    def tearDown(self):

        # Remove our test folder for UserManager data
        if os.path.exists(self._userDataDir):
            shutil.rmtree(self._userDataDir, ignore_errors=True)
        self._mgr = None


    def testUsersNoRoles(self):
        from UserKit.UserManagerToFile import UserManagerToFile

        self._mgr = UserManagerToFile()
        self.setUpDataDir(self._mgr)

        # Create a user, add to 'staff' role
        fooUser = self._mgr.createUser('foo', 'bar')

        # bad login
        theUser = self._mgr.loginName('foo', 'badpass')
        self.assertTrue(theUser is None,
            'loginName() returns null if login failed.')
        self.assertFalse(fooUser.isActive(),
            'User should NOT be logged in since password was incorrect.')

        # good login
        theUser = self._mgr.loginName('foo', 'bar')
        self.assertTrue(theUser.isActive(), 'User should be logged in now')
        self.assertEqual(theUser, fooUser,
            'Should be the same user object, since it is the same user "foo"')

        # logout
        theUser.logout()
        self.assertFalse(theUser.isActive(),
            'User should no longer be active.')
        self.assertEqual(self._mgr.numActiveUsers(), 0)


    def testUsersAndRoles(self):
        from UserKit.RoleUserManagerToFile import RoleUserManagerToFile
        from UserKit.HierRole import HierRole
        from hashlib import sha1 as sha

        self._mgr = RoleUserManagerToFile()
        self.setUpDataDir(self._mgr)

        # Setup our roles
        customersRole = HierRole('customers', 'Customers of ACME Industries')
        staffRole = HierRole('staff', 'All staff.'
            ' Staff role includes all permissions of Customers role.',
            [customersRole])

        # Create a user, add to 'staff' role
        # Note that I encrypt my passwords here so they don't appear
        # in plaintext in the storage file.
        johnUser = self._mgr.createUser('john', sha('doe').hexdigest())
        johnUser.setRoles([customersRole])

        fooUser = self._mgr.createUser('foo', sha('bar').hexdigest())
        fooUser.setRoles([staffRole])

        # Check user "foo"
        theUser = self._mgr.loginName('foo', sha('bar').hexdigest())
        self.assertTrue(theUser.isActive(), 'User should be logged in now')
        self.assertEqual(theUser, fooUser,
            'Should be the same user object, since it is the same user "foo"')
        self.assertTrue(theUser.playsRole(staffRole),
            'User "foo" should be a member of the staff role.')
        self.assertTrue(theUser.playsRole(customersRole), 'User "foo" should'
            ' also be in customer role, since staff includes customers.')

        # Check user "John"
        theUser = self._mgr.loginName('john', sha('doe').hexdigest())
        self.assertTrue(theUser.isActive(), 'User should be logged in now.')
        self.assertEqual(theUser, johnUser, 'Should be the same user object,'
            ' since it is the same user "John".')
        self.assertFalse(theUser.playsRole(staffRole),
            'John should not be a member of the staff.')
        self.assertTrue(theUser.playsRole(customersRole),
            'John should play customer role.')


if __name__ == '__main__':
    unittest.main()
