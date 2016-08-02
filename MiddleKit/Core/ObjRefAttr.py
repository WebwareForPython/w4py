from Attr import Attr


def objRefJoin(klassId, serialNum):
    """Given a klass id and object serial number, return a 64-bit obj ref value (e.g., a long)."""
    return (long(klassId) << 32) | long(serialNum)

def objRefSplit(objRef):
    """Return a tuple with (klassId, serialNum) given the 64-bit (e.g., long type) objRef."""
    return (objRef & 0xFFFFFFFF00000000L) >> 32, objRef & 0xFFFFFFFFL


class ObjRefAttr(Attr):
    """This is an attribute that refers to another user-defined object.

    For a list of objects, use ListAttr.
    """

    def __init__(self, attr):
        Attr.__init__(self, attr)
        self._className = attr['Type']

    def targetClassName(self):
        """Return the name of the base class that this obj ref attribute points to."""
        return self._className

    def targetKlass(self):
        assert self._targetKlass, 'not yet fully initialized'
        return self._targetKlass

    def awakeFromRead(self):
        """Check that the target class actually exists."""
        self._targetKlass = self.model().klass(self.targetClassName(), None)
        if not self._targetKlass:
            from Model import ModelError
            raise ModelError('class %s: attr %s:'
                'cannot locate target class %s for this obj ref.' % (
                self.klass().name(), self.name(), self.targetClassName()))
