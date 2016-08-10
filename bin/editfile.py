#!/usr/bin/env python

"""Helper script for the feature provided by the IncludeEditLink setting."""

editor = 'Vim'

editorCommands = {
    'Emacs':
        'gnuclient +%(line)s "%(filename)s"',
    'Geany':
        'geany -l %(line)s "%(filename)s"',
    'Geany (Windows)':
        r'start %%ProgramFiles%%\Geany\Geany.exe -l %(line)s "%(filename)s"',
    'gedit':
        'gedit +%(line)s "%(filename)s"',
    'jEdit':
        'jedit "%(filename)s" +line:%(line)s',
    'jedit (Windows)':
        'start %%ProgramFiles%%\\jEdit\jedit.jar "%(filename)s" +line:%(line)s',
    'Kate':
        'kate -u -l %(line)s "%(filename)s"',
    'Komodo':
        'komodo -l %(line)s "%(filename)s"',
    'Komodo Edit 5 (Windows)':
        r'start %%ProgramFiles%%\"ActiveState Komodo Edit 5"\komodo.exe -l %(line)s "%(filename)s"',
    'Komodo IDE 5 (Windows)':
        r'start %%ProgramFiles%%\"ActiveState Komodo IDE 5"\komodo.exe -l %(line)s "%(filename)s"',
    'KWrite':
        'kwrite --line %(line)s "%(filename)s"',
    'Notepad++ (Windows)':
        r'start %%ProgramFiles%%\Notepad++\notepad++.exe -n%(line)s "%(filename)s"',
    'PSPad (Windows)':
        r'start %%ProgramFiles%%\PSPad\PSPad.exe -%(line)s "%(filename)s"',
    'SciTE':
        'scite "%(filename)s" -goto:%(line)s',
    'SciTE (Windows)':
        r'start %%ProgramFiles%%\SciTE\SciTE.exe "%(filename)s" -goto:%(line)s',
    'Vim':
        'gvim +%(line)s "%(filename)s"',
    }

defaultCommand = editor + ' +%(line)s "%(filename)s"'

import os
import sys
try:
    from email import message_from_file
except ImportError:
    from rfc822 import Message as message_from_file


def transform(params):
    """Transform EditFile paramters.

    As an example, if you are under Windows and your edit file
    has a Unix filename, then it is transformed to a Samba path.
    """
    filename = params['filename']
    if os.sep == '\\' and filename.startswith('/'):
        filename = os.path.normpath(filename[1:])
        hostname = params['hostname'].split(':', 1)[0]
        sambapath = r'\\%s\root' % hostname
        filename = os.path.join(sambapath, filename)
        params['filename'] = filename
    return params


def openFile(params):
    """Open editor with file specified in parameters."""
    command = editorCommands.get(editor, defaultCommand) % transform(params)
    print command
    os.system(command)


def parseFile(filename):
    """Parse the WebKit EditFile."""
    openFile(message_from_file(open(filename)))


if __name__ == '__main__':
    parseFile(sys.argv[1])
