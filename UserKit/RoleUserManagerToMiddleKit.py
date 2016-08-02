"""The RoleUserManagerToMiddleKit class."""

from RoleUserManagerMixIn import RoleUserManagerMixIn
from UserManagerToMiddleKit import UserManagerToMiddleKit


class RoleUserManagerToMiddleKit(RoleUserManagerMixIn, UserManagerToMiddleKit):
    """See the base classes for more information."""

    def __init__(self, userClass=None, store=None, useSQL=None):
        UserManagerToMiddleKit.__init__(self, userClass, store, useSQL)
        RoleUserManagerMixIn.__init__(self)

    def initUserClass(self):
        """Invoked by __init__ to set the default user class.

        Overridden to pass on the semantics we inherit from
        RoleUsersManagerMixIn. The user class is a MiddleKit issue for us.
        """
        pass
