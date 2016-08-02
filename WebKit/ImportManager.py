"""ImportManager

Manages imported modules and protects against concurrent imports.

Keeps lists of all imported Python modules and templates as well as other
config files used by Webware for Python. For modules which are not directly
imported, ImportManager can use ImportSpy to keep track of them. This can
be used to detect changes in source files, templates or config files in order
to reload them automatically by the AutoReloadingAppServer. The use of
ImportSpy can be suppressed with the``UseImportSpy`` setting.
"""

import imp
import os
import sys


class ImportManager(object):
    """The import manager.

    Keeps track of the Python modules and other system files that have been
    imported and are used by Webware.
    """

    _imp = _spy = None

    def __init__(self):
        """Create import hook."""
        assert not self._imp, "Only one instance of ImportManager is possible."
        self._imp = True
        self._fileList = {}
        self._moduleFiles = {}
        self._notifyHook = None

    def load_module(self, name, file, filename, info):
        """Replaces imp.load_module."""
        try:
            try:
                imp.acquire_lock()
                mod = imp.load_module(name, file, filename, info)
            finally:
                imp.release_lock()
                if file:
                    file.close()
            self.recordModule(mod)
        except:
            # Also record filepaths which weren't successfully loaded, which
            # may happen due to a syntax error in a servlet, because we also
            # want to know when such a file is modified:
            self.recordFile(filename)
            raise
        return mod

    @staticmethod
    def find_module(name, path=None):
        """Replaces imp.find_module."""
        return imp.find_module(name, path)

    def activateImportSpy(self):
        """Activate ImportSpy to keep track of modules loaded elsewhere."""
        if not self._spy:
            from ImportSpy import activate
            activate(self)
            self._spy = True

    def fileList(self, update=True):
        """Return the list of tracked files."""
        if not self._spy and update:
            # Update list of files of imported modules
            moduleNames = []
            for modname in sys.modules:
                if modname not in self._moduleFiles:
                    moduleNames.append(modname)
            if moduleNames:
                self.recordModules(moduleNames)
        return self._fileList

    def notifyOfNewFiles(self, hook):
        """Register notification hook.

        Called by someone else to register that they'd like to be know
        when a new file is imported.
        """
        self._notifyHook = hook

    def watchFile(self, path, modname=None, getmtime=os.path.getmtime):
        """Add more files to watch without importing them."""
        modtime = getmtime(path)
        self._fileList[path] = modtime
        if modname:
            self._moduleFiles[modname] = path
        # send notification that this file was imported
        if self._notifyHook:
            self._notifyHook(path, modtime)

    def recordModule(self, mod, isfile=os.path.isfile):
        """Record a module."""
        modname = getattr(mod, '__name__', None)
        if not modname or modname not in sys.modules:
            return
        fileList = self._fileList
        # __orig_file__ is used for PSP, Kid and Cheetah templates; we want
        # to record the source filenames, not the auto-generated modules:
        f = getattr(mod, '__orig_file__', None)
        if f and f not in fileList:
            try:
                if isfile(f):
                    self.watchFile(f, modname)
            except OSError:
                pass
        else:
            f = getattr(mod, '__file__', None)
            if f and f not in fileList:
                # record the .py file corresponding to each .pyc or .pyo
                if f[-4:].lower() in ('.pyc', '.pyo'):
                    f = f[:-1]
                try:
                    if isfile(f):
                        self.watchFile(f, modname)
                    else:
                        self.watchFile(os.path.join(f, '__init__.py'))
                except OSError:
                    pass

    def recordModules(self, moduleNames=None):
        """Record a list of modules (or all modules)."""
        if moduleNames is None:
            moduleNames = sys.modules
        for modname in moduleNames:
            mod = sys.modules[modname]
            self.recordModule(mod)

    def recordFile(self, filename, isfile=os.path.isfile):
        """Record a file."""
        if isfile(filename):
            self.watchFile(filename)

    def fileUpdated(self, filename, update=True, getmtime=os.path.getmtime):
        """Check whether file has been updated."""
        fileList = self.fileList(update)
        try:
            mtime = fileList[filename]
        except KeyError:
            return True
        try:
            newmtime = getmtime(filename)
        except OSError:
            return True
        if mtime >= newmtime:
            return False
        fileList[filename] = newmtime
        # Note that the file list could be changed while running this
        # method in a monitor thread, so we don't use iteritems() here:
        for modname, modfile in self._moduleFiles.items():
            if modfile == filename:
                mod = sys.modules.get(modname)
                return not mod or not getattr(mod, '__donotreload__', False)
        return True  # it's not a module, we must reload

    def updatedFile(self, update=True, getmtime=os.path.getmtime):
        """Check whether one of the files has been updated."""
        fileList = self.fileList(update)
        for filename, mtime in fileList.items():
            try:
                newmtime = getmtime(filename)
            except OSError:
                return filename
            if mtime >= newmtime:
                continue
            fileList[filename] = newmtime
            for modname, modfile in self._moduleFiles.items():
                if modfile == filename:
                    mod = sys.modules.get(modname)
                    if mod and getattr(mod, '__donotreload__', False):
                        break
                    return filename  # it's a module that needs to be reloaded
            else:
                return filename  # it's not a module, we must reload

    def delModules(self, includePythonModules=False, excludePrefixes=None):
        """Delete imported modules.

        Deletes all the modules that the ImportSpy has ever imported unless
        they are part of WebKit. This in support of DebugAppServer's useful
        (yet imperfect) support for AutoReload.
        """
        moduleFiles = self._moduleFiles
        fileList = self._fileList
        for modname in moduleFiles:
            if modname == __name__:
                continue
            filename = self._moduleFiles[modname]
            if not includePythonModules:
                if not filename or filename.startswith(sys.prefix):
                    continue
            for prefix in excludePrefixes or []:
                if modname.startswith(prefix):
                    break
            else:
                try:
                    del sys.modules[modname]
                except KeyError:
                    pass
                try:
                    del moduleFiles[modname]
                except KeyError:
                    pass
                try:
                    del fileList[filename]
                except KeyError:
                    pass
