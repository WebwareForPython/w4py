import re

from ModelObject import ModelObject
from MiscUtils import NoDefault
from MiddleDict import MiddleDict


nameRE = re.compile('^([A-Za-z_][A-Za-z_0-9]*)$')
reservedRE = re.compile('allattrs|changed|clone|debugstr|dumpattrs|key|klass'
    '|serialnum|store|valueforattr|valueforkey', re.I)


class Attr(MiddleDict, ModelObject):
    """An Attr represents an attribute of a Klass.

    The Attr objects behave like dictionaries.
    """

    def __init__(self, attr):
        MiddleDict.__init__(self, {})
        for key, value in attr.items():
            if key == 'Attribute':
                key = 'Name'
            if isinstance(value, basestring) and not value.strip():
                value = None
            self[key] = value
        name = self['Name']
        match = nameRE.match(name)
        if match is None or len(match.groups()) != 1:
            raise ValueError('Bad name (%r) for attribute: %r.' % (name, attr))
        match = reservedRE.match(name)
        if match is not None:
            raise ValueError('Reserved name (%r) for attribute: %r.' % (name, attr))
        self._getPrefix = None
        self._setPrefix = None

    def name(self):
        return self['Name']

    def isRequired(self):
        """Return true if a value is required for this attribute.

        In Python, that means the value cannot be None. In relational theory
        terms, that means the value cannot be NULL.
        """
        return self.boolForKey('isRequired')

    def setKlass(self, klass):
        """Set the klass that the attribute belongs to."""
        self._klass = klass

    def klass(self):
        """Return the klass that this attribute is declared in and, therefore, belongs to."""
        return self._klass

    def pyGetName(self):
        """Return the name that should be used for the Python "get" accessor method for this attribute."""
        if self._getPrefix is None:
            self._computePrefixes()
        name = self.name()
        if self._getCapped:
            return self._getPrefix + name[0].upper() + name[1:]
        else:
            return self._getPrefix + name

    def pySetName(self):
        """Return the name that should be used for the Python "set" accessor method for this attribute."""
        if self._setPrefix is None:
            self._computePrefixes()
        name = self.name()
        if self._setCapped:
            return self._setPrefix + name[0].upper() + name[1:]
        else:
            return self._setPrefix + name

    def setting(self, name, default=NoDefault):
        """Return the value of a particular configuration setting taken from the model.

        Implementation note: Perhaps a future version should ask the klass and so on up the chain.
        """
        return self.model().setting(name, default)

    def model(self):
        return self._klass.klasses()._model

    def awakeFromRead(self):
        pass


    ## Warnings ##

    def printWarnings(self, out):
        pass


    ## Self Util ##

    def _computePrefixes(self):
        style = self.setting('AccessorStyle', 'methods').lower()
        assert style in ('properties', 'methods')
        if style == 'properties':
            self._getPrefix = '_get_'
            self._setPrefix = '_set_'
            self._getCapped = False
            self._setCapped = False
        else:
            # methods
            self._getPrefix = ''
            self._setPrefix = 'set'
            self._getCapped = False
            self._setCapped = True
