"""The basic Role class."""

from MiscUtils.Funcs import positiveId


class Role(object):
    """Used in conjuction with RoleUser to provide role-based security.

    All roles have a name and a description and respond to playsRole().

    RoleUser also responds to playsRole() and is the more popular entry point
    for programmers. Application code may then do something along the lines of:

    if user.playsRole('admin'):
        self.displayAdminMenuItems()

    See also:
      * class HierRole
      * class RoleUser
    """


    ## Init ##

    def __init__(self, name, description=None):
        self._name = name
        self._description = description

    def __str__(self):
        return self.name()


    ## Attributes ##

    def name(self):
        return self._name

    def setName(self, name):
        self._name = name

    def description(self):
        return self._description

    def setDescription(self, description):
        self._description = description


    ## As strings ##

    def __str__(self):
        return str(self._name)

    def __repr__(self):
        return '<%s %r instance at %x>' % (
            self.__class__, self._name, positiveId(self))


    ## The big question ##

    def playsRole(self, role):
        """Return true if the receiving role plays the role passed in.

        For Role, this is simply a test of equality. Subclasses may override
        this method to provide richer semantics (such as hierarchical roles).
        """
        if not isinstance(role, Role):
            raise TypeError('%s is not a Role object' % (role,))
        return self == role
