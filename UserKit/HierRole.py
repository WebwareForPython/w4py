"""The HierRole class."""

from Role import Role


class HierRole(Role):
    """HierRole is a hierarchical role.

    It points to its parent roles. The hierarchy cannot have cycles.
    """

    def __init__(self, name, description=None, superRoles=[]):
        Role.__init__(self, name, description)
        for role in superRoles:
            if not isinstance(role, Role):
                raise TypeError('%s is not a Role object' % (role,))
        self._superRoles = superRoles[:]

    def playsRole(self, role):
        """Check whether the receiving role plays the role that is passed in.

        This implementation provides for the inheritance that HierRole supports.
        """
        if self == role:
            return True
        for superRole in self._superRoles:
            if superRole.playsRole(role):
                return True
        else:
            return False
