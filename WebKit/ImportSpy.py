"""ImportSpy

Keeps track of modules not imported directly by Webware for Python.

This module helps save the filepath of every module which is imported.
This is used by the `AutoReloadingAppServer` (see doc strings for more
information) to restart the server if any source files change.

Other than keeping track of the filepaths, the behaviour of this module
loader is identical to Python's default behaviour.

If the system supports FAM (file alteration monitor) and python-fam is
installed, then the need for reloading can be monitored very effectively
with the use of ImportSpy. Otherwise, ImportSpy will not have much benefit.

Note that ImportSpy is based on the new import hooks of Python described
in PEP 302. It is possible to suppress the use of ImportSpy by setting
`UseImportSpy` in AppServer.config to False.
"""

from os.path import isdir
from sys import path_hooks, path_importer_cache


class ImportSpy(object):
    """New style import tracker."""

    _imp = None

    def __init__(self, path=None):
        """Create importer."""
        assert self._imp
        if path and isdir(path):
            self.path = path
        else:
            raise ImportError

    def find_module(self, fullname):
        """Replaces imp.find_module."""
        try:
            self.file, self.filename, self.info = self._imp.find_module(
                fullname.rsplit('.', 1)[-1], [self.path])
        except ImportError:
            pass
        else:
            return self

    def load_module(self, fullname):
        """Replaces imp.load_module."""
        mod = self._imp.load_module(fullname, self.file, self.filename, self.info)
        if mod:
            mod.__loader__ = self
        return mod


def activate(impManager):
    """Activate ImportSpy."""
    assert not ImportSpy._imp
    ImportSpy._imp = impManager
    path_hooks.append(ImportSpy)
    path_importer_cache.clear()
    impManager.recordModules()
