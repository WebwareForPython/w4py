
"""This module handles requests from the application for PSP pages.

(c) Copyright by Jay Love, 2000 (mailto:jsliv@jslove.org)

Permission to use, copy, modify, and distribute this software and its
documentation for any purpose and without fee or royalty is hereby granted,
provided that the above copyright notice appear in all copies and that
both that copyright notice and this permission notice appear in
supporting documentation or portions thereof, including modifications,
that you make.
"""

import os
import sys
from glob import glob
from string import digits, letters

from WebKit.ServletFactory import ServletFactory
from PSP import Context, PSPCompiler


class PSPServletFactory(ServletFactory):
    """Servlet Factory for PSP files."""

    def __init__(self, application):
        ServletFactory.__init__(self, application)
        self._cacheDir = os.path.join(application._cacheDir, 'PSP')
        sys.path.append(self._cacheDir)
        self._cacheClassFiles = self._cacheClasses
        t = ['_'] * 256
        for c in digits + letters:
            t[ord(c)] = c
        self._classNameTrans = ''.join(t)
        setting = application.setting
        self._extensions = setting('ExtensionsForPSP', ['.psp'])
        self._fileEncoding = setting('PSPFileEncoding', None)
        if setting('ClearPSPCacheOnStart', False):
            self.clearFileCache()
        self._recordFile = application._imp.recordFile

    def uniqueness(self):
        return 'file'

    def extensions(self):
        return self._extensions

    def fileEncoding(self):
        """Return the file encoding used in PSP files."""
        return self._fileEncoding

    def flushCache(self):
        """Clean out the cache of classes in memory and on disk."""
        ServletFactory.flushCache(self)
        self.clearFileCache()

    def clearFileCache(self):
        """Clear class files stored on disk."""
        files = glob(os.path.join(self._cacheDir, '*.*'))
        map(os.remove, files)

    def computeClassName(self, pagename):
        """Generates a (hopefully) unique class/file name for each PSP file.

        Argument: pagename: the path to the PSP source file
        Returns: a unique name for the class generated fom this PSP source file
        """
        # Compute class name by taking the path and substituting
        # underscores for all non-alphanumeric characters:
        return os.path.splitdrive(pagename)[1].translate(self._classNameTrans)

    def loadClassFromFile(self, transaction, filename, classname):
        """Create an actual class instance.

        The module containing the class is imported as though it were a
        module within the context's package (and appropriate subpackages).
        """
        module = self.importAsPackage(transaction, filename)
        assert classname in module.__dict__, (
            'Cannot find expected class named %r in %r.'
            % (classname, filename))
        theClass = getattr(module, classname)
        return theClass

    def loadClass(self, transaction, path):
        classname = self.computeClassName(path)
        classfile = os.path.join(self._cacheDir, classname + ".py")
        mtime = os.path.getmtime(path)
        if (not os.path.exists(classfile)
                or os.path.getmtime(classfile) != mtime):
            context = Context.PSPCLContext(path)
            context.setClassName(classname)
            context.setPythonFileName(classfile)
            context.setPythonFileEncoding(self._fileEncoding)
            clc = PSPCompiler.Compiler(context)
            sourcefiles = clc.compile()
            # Set the modification time of the compiled file
            # to be the same as the source file;
            # that's how we'll know if it needs to be recompiled:
            os.utime(classfile, (os.path.getatime(classfile), mtime))
            # Record all included files so we can spot any changes:
            for sourcefile in sourcefiles:
                self._recordFile(sourcefile)
        theClass = self.loadClassFromFile(transaction, classfile, classname)
        return theClass
