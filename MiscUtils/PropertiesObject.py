import os
import sys


class WillNotRunError(Exception):
    """Error for Webware components that will not run."""


class PropertiesObject(dict):
    """A Properties Object.

    A PropertiesObject represents, in a dictionary-like fashion, the values
    found in a Properties.py file. That file is always included with a Webware
    component to advertise its name, version, status, etc. Note that a Webware
    component is a Python package that follows additional conventions.
    Also, the top level Webware directory contains a Properties.py.

    Component properties are often used for:
      * generation of documentation
      * runtime examination of components, especially prior to loading

    PropertiesObject provides additional keys:
      * filename - the filename from which the properties were read
      * versionString - a nicely printable string of the version
      * requiredPyVersionString - like versionString,
        but for requiredPyVersion instead
      * willRun - 1 if the component will run.
        So far that means having the right Python version.
      * willNotRunReason - defined only if willRun is 0,
        contains a readable error message

    Using a PropertiesObject is better than investigating the Properties.py
    file directly, because the rules for determining derived keys and any
    future convenience methods will all be provided here.

    Usage example:
        from MiscUtils.PropertiesObject import PropertiesObject
        props = PropertiesObject(filename)
        for item in props.items():
            print '%s: %s' % item

    Note: We don't normally suffix a class name with "Object" as we have
    with this class, however, the name Properties.py is already used in
    our containing package and all other packages.
    """


    ## Init and reading ##

    def __init__(self, filename=None):
        dict.__init__(self)
        if filename:
            self.readFileNamed(filename)

    def loadValues(self, *args, **kwargs):
        self.update(*args, **kwargs)
        self.cleanPrivateItems()

    def readFileNamed(self, filename):
        results = {}
        exec open(filename) in results
        self.update(results)
        self.cleanPrivateItems()
        self.createDerivedItems()


    ## Self utility ##

    def cleanPrivateItems(self):
        """Remove items whose keys start with a double underscore, such as __builtins__."""
        for key in self.keys():  # must use keys() because dict is changed
            if key.startswith('__'):
                del self[key]

    def createDerivedItems(self):
        self.createVersionString()
        self.createRequiredPyVersionString()
        self.createWillRun()

    def _versionString(self, version):
        """Return the version number as a string.

        For a sequence containing version information such as (2, 0, 0, 'pre'),
        this returns a printable string such as '2.0pre'.
        The micro version number is only excluded from the string if it is zero.
        """
        ver = map(str, version)
        numbers, rest = ver[:2 if ver[2] == '0' else 3], ver[3:]
        return '.'.join(numbers) + '-'.join(rest)

    def createVersionString(self):
        self['versionString'] = self._versionString(self['version'])

    def createRequiredPyVersionString(self):
        self['requiredPyVersionString'] = self._versionString(self['requiredPyVersion'])

    def createWillRun(self):
        self['willRun'] = False
        try:
            # Invoke each of the checkFoo() methods
            for key in self.willRunKeys():
                methodName = 'check' + key[0].upper() + key[1:]
                method = getattr(self, methodName)
                method()
        except WillNotRunError as msg:
            self['willNotRunReason'] = msg
            return
        self['willRun'] = 1  # we passed all the tests

    def willRunKeys(self):
        """Return keys to be examined before running the component.

        This returns a set of all keys whose values should be examined in
        order to determine if the component will run. Used by createWillRun().
        """
        return set(('requiredPyVersion', 'requiredOpSys', 'deniedOpSys', 'willRunFunc'))

    def checkRequiredPyVersion(self):
        if tuple(sys.version_info) < tuple(self['requiredPyVersion']):
            raise WillNotRunError('Required Python version is %s,'
                ' but actual version is %s.' % (
                '.'.join(map(str, self['requiredPyVersion'])),
                '.'.join(map(str, sys.version_info))))

    def checkRequiredOpSys(self):
        requiredOpSys = self.get('requiredOpSys')
        if requiredOpSys:
            # We accept a string or list of strings
            if isinstance(requiredOpSys, basestring):
                requiredOpSys = [requiredOpSys]
            if not os.name in requiredOpSys:
                raise WillNotRunError('Required operating system is %s,'
                    ' but actual operating system is %s.' % (
                    '/'.join(requiredOpSys), os.name))

    def checkDeniedOpSys(self):
        deniedOpSys = self.get('deniedOpSys')
        if deniedOpSys:
            # We accept a string or list of strings
            if isinstance(deniedOpSys, basestring):
                deniedOpSys = [deniedOpSys]
            if os.name in deniedOpSys:
                raise WillNotRunError('Will not run on operating system %s'
                    ' and actual operating system is %s.' % (
                    '/'.join(deniedOpSys), os.name))

    def checkRequiredSoftware(self):
        """Not implemented. No op right now."""
        # Check required software
        # @@ 2001-01-24 ce: TBD
        # Issues include:
        #  - order of dependencies
        #  - circular dependencies
        #  - examining Properties and willRun of dependencies
        reqSoft = self.get('requiredSoftware')
        if reqSoft:
            for soft in reqSoft:
                # type, name, version
                pass

    def checkWillRunFunc(self):
        willRunFunc = self.get('willRunFunc')
        if willRunFunc:
            whyNotMsg = willRunFunc()
            if whyNotMsg:
                raise WillNotRunError(whyNotMsg)
