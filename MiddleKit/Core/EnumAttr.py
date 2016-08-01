from Attr import Attr


class EnumAttr(Attr):

    def __init__(self, attr):
        Attr.__init__(self, attr)
        # We expect that an 'Enums' key holds the enumeration values
        self._enums = [enum.strip() for enum in self['Enums'].split(',')]
        self._enumSet = dict((enum, i) for i, enum in enumerate(self._enums))

    def enums(self):
        """Return a sequence of the enum values in their string form."""
        return self._enums

    def hasEnum(self, value):
        if isinstance(value, basestring):
            return value in self._enumSet
        else:
            return 0 <= value < len(self._enums)

    def intValueForString(self, s):
        return self._enumSet[s]
