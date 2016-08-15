#!/usr/bin/env python

"""FileList.py

A quick, hacky script to construct a file list from a set of Python files.
"""


import os
import sys
from glob import glob


class FileList(object):
    """Builds a file list for a package of Python modules."""

    def __init__(self, name='Webware'):
        self._name = name
        self._files = []
        self._verbose = False
        self._filesToIgnore = []

    def addFilesToIgnore(self, list):
        self._filesToIgnore.extend(list)

    def readFiles(self, filename):
        filenames = glob(filename)
        for name in filenames:
            self.readFile(name)

    def readFile(self, name):
        if name in self._filesToIgnore:
            if self._verbose:
                print 'Skipping %s...' % name
            return
        if self._verbose:
            print 'Reading %s...' % name
        self._files.append(name)

    def printList(self, file=sys.stdout):
        if isinstance(file, basestring):
            file = open(file, 'w')
            closeFile = True
        else:
            closeFile = False
        name = self._name
        title = 'File List of %s' % name
        file.write('%s\n%s\n\n' % (title, '='*len(title)))
        for filename in sorted(self._files, key=lambda f: f.lower()):
            file.write(filename + '\n')
        file.write('\n')
        if closeFile:
            file.close()

    def printForWeb(self, file=sys.stdout):
        if isinstance(file, basestring):
            file = open(file, 'w')
            closeFile = True
        else:
            closeFile = False
        name = self._name
        title = 'File List of %s' % name
        other = ('<a href="ClassList.html">alphabetical class list</a>'
            ' and <a href="ClassHierarchy.html">class hierarchy</a>'
            ' of %s' % name)
        file.write('''<!DOCTYPE html>
<head>
<title>%s</title>
<style type="text/css">
<!--
body { background: #FFF;
font-family: Verdana, Arial, Helvetica, sans-serif;
font-size: 10pt;
padding: 6pt; }
table { empty-cells: show;
border-spacing: 2px; border-collapse: separate; border-style: none; }
th { background-color: #CCF; text-align: left;
padding: 2px; border-style: none; }
td { background-color: #EEF;
padding: 2px; border-style: none; }
.center { text-align: center; }
.center table { margin-left: auto; margin-right: auto; text-align: left; }
-->
</style>
</head>
<body><div class="center">
<h1>%s</h1>
<p>See also the %s.</p>
<table>
''' % (title, title, other))
        file.write('<tr><th>Source File</th>'
            '<th>Source</th><th>Doc</th><th>Summary</th></tr>\n')
        for filename in sorted(self._files, key=lambda f: f.lower()):
            file.write('<tr><td>%s</td></tr>\n' % self.links(filename))
        file.write('''</table>
</div></body>
</html>''')
        if closeFile:
            file.close()

    def links(self, filename):
        """In support of printForWeb()"""
        name = self._name
        links = []
        # source file
        if os.path.exists(filename):
            links.append('<a href="../../%s">%s</a>' % (filename, filename))
        else:
            links.append('&nbsp;')
        filename = os.path.basename(filename)
        module = os.path.splitext(filename)[0]
        # highlighted source file
        if os.path.exists('Docs/Source/Files/%s.html' % module):
            links.append('<a href="Files/%s.html">source</a>' % module)
        else:
            links.append('&nbsp;')
        # doc file
        if os.path.exists('Docs/Source/Docs/%s.%s.html' % (name, module)):
            links.append('<a href="Docs/%s.%s.html">doc</a>' % (name, module))
        else:
            links.append('&nbsp;')
        # summary file
        if os.path.exists('Docs/Source/Summaries/%s.html' % module):
            links.append('<a href="Summaries/%s.html">summary</a>' % module)
        else:
            links.append('&nbsp;')
        # finish up
        return '</td><td class="center">'.join(links)


def main(args):
    filelist = FileList()
    for filename in args:
        filelist.readFiles(filename)
    filelist.printList()


if __name__ == '__main__':
    main(sys.argv[1:])
