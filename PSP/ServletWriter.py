
"""This module holds the actual file writer class.

(c) Copyright by Jay Love, 2000 (mailto:jsliv@jslove.org)

Permission to use, copy, modify, and distribute this software and its
documentation for any purpose and without fee or royalty is hereby granted,
provided that the above copyright notice appear in all copies and that
both that copyright notice and this permission notice appear in
supporting documentation or portions thereof, including modifications,
that you make.

This software is based in part on work done by the Jakarta group.
"""

import os
from tempfile import mkstemp


class ServletWriter(object):
    """This file creates the servlet source code.

    Well, it writes it out to a file at least.
    """

    _tab = '\t'
    _spaces = '    '  # 4 spaces
    _emptyString = ''

    def __init__(self, ctxt):
        self._pyfilename = ctxt.getPythonFileName()
        fd, self._temp = mkstemp('tmp', dir=os.path.dirname(self._pyfilename))
        self._filehandle = os.fdopen(fd, 'w')
        self._tabcnt = 0
        self._blockcount = 0  # a hack to handle nested blocks of python code
        self._indentSpaces = self._spaces
        self._useTabs = False
        self._useBraces = False
        self._indent = '    '
        self._userIndent = self._emptyString
        self._awakeCreated = False  # means that awake() needs to be generated

    def setIndentSpaces(self, amt):
        self._indentSpaces = ' ' * amt
        self.setIndention()

    def setIndention(self):
        if self._useTabs:
            self._indent = '\t'
        else:
            self._indent = self._indentSpaces

    def setIndentType(self, type):
        if type == 'tabs':
            self._useTabs = True
            self.setIndention()
        elif type == 'spaces':
            self._useTabs = False
            self.setIndention()
        elif type == 'braces':
            self._useTabs = False
            self._useBraces = True
            self.setIndention()

    def close(self):
        self._filehandle.close()
        if os.path.exists(self._pyfilename):
            os.remove(self._pyfilename)
        try:
            os.rename(self._temp, self._pyfilename)
        except OSError:
            # The operation may fail on some Unix flavors
            # if the files are on different filesystems.
            # In this case, we try to move the files manually:
            with open(self._pyfilename, 'wb') as f:
                f.write(open(self._temp, 'rb').read())
            os.remove(self._temp)

    def pushIndent(self):
        """this is very key, have to think more about it"""
        self._tabcnt += 1

    def popIndent(self):
        if self._tabcnt > 0:
            self._tabcnt -= 1

    def printComment(self, start, stop, chars):
        if start and stop:
            self.println('## from ' + str(start))
            self.println('## from ' + str(stop))
        if chars:
            lines = chars.splitlines()
            for line in lines:
                self._filehandle.write(self.indent(''))
                self._filehandle.write('##')
                self._filehandle.write(line)

    def quoteString(self, s):
        """Escape the string."""
        if s is None:
            # this probably won't work, I'll be back for this
            return 'None'
        return 'r' + s

    def indent(self, s):
        """Indent the string."""
        if self._userIndent or self._tabcnt > 0:
            return self._userIndent + self._indent*self._tabcnt + s
        return s

    def println(self, line=None):
        """Print with indentation and a newline if none supplied."""
        if line:
            self._filehandle.write(self.indent(line))
            if not line.endswith('\n'):
                self._filehandle.write('\n')
        else:
            self._filehandle.write(self.indent('\n'))

    def printChars(self, s):
        """Just prints what its given."""
        self._filehandle.write(s)

    def printMultiLn(self, s):
        raise NotImplementedError

    def printList(self, strlist):
        """Prints a list of strings with indentation and a newline."""
        for line in strlist:
            self.printChars(self.indent(line))
            self.printChars('\n')

    def printIndent(self):
        """Just prints tabs."""
        self.printChars(self.indent(''))
