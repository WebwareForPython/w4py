#!/usr/bin/env python

"""Dump.py

> python Dump.py -h
"""


import os
import sys
from getopt import getopt


def FixPathForMiddleKit(verbose=0):
    """Enhance sys.path so that Dump.py can import MiddleKit.whatever.

    We *always* enhance the sys.path so that Dump.py is using the MiddleKit
    that contains him, as opposed to whatever happens to be found first
    in the Python path. That's an subtle but important feature for those of us
    who sometimes have more than one MiddleKit on our systems.
    """
    v = verbose
    if '__file__' in globals():
        # We were imported as a module
        location = __file__
        if v:
            print 'took location from __file__'
    else:
        # We were executed directly
        location = sys.argv[0]
        if v:
            print 'took location from sys.argv[0]'

    if v:
        print 'location =', location
    if location.lower() == 'dump.py':
        # The simple case. We're at MiddleKit/Design/Dump.py
        location = os.path.abspath('../../')
    else:
        # location will basically be:
        # .../MiddleKit/Design/Dump.py
        if os.name == 'nt':
            # Case insenstive file systems:
            location = location.lower()
            what = 'middlekit'
        else:
            what = 'MiddleKit'
        if what in location:
            if v:
                print 'MiddleKit in location'
            index = location.index(what)
            location = location[:index]
            if v:
                print 'new location =', location
        location = os.path.abspath(location)
        if v:
            print 'final location =', location
    sys.path.insert(1, location)
    if v:
        print 'path =', sys.path
        print
        print 'importing MiddleKit...'
    import MiddleKit
    if v:
        print 'done.'

FixPathForMiddleKit()
import MiddleKit


class Dump(object):

    def databases(self):
        """Return a list with the names of the supported database engines."""
        return ['MSSQL', 'MySQL', 'PostgreSQL', 'SQLite']

    def main(self, args=sys.argv):
        """Main method."""
        opt = self.options(args)

        if 'outfile' in opt:
            out = open(opt['outfile'], 'w')
        else:
            out = None

        # this is really only necessary if 'package' is set for the model,
        # but it shouldn't hurt
        middledir = os.path.dirname(os.path.dirname((os.path.abspath(opt['model']))))
        sys.path.insert(1, middledir)

        # Dump
        classname = '%sObjectStore' % opt['db']
        module = __import__('MiddleKit.Run.%s' % classname, globals(), locals(), [classname])
        pyClass = getattr(module, classname)
        if 'prompt-for-args' in opt:
            sys.stderr.write('Enter %s init args: ' % classname)
            conn = raw_input()
            store = eval('pyClass(%s)' % conn)
        else:
            store = pyClass()
        store.readModelFileNamed(opt['model'])
        store.dumpObjectStore(out, progress='show-progress' in opt)

    def usage(self, errorMsg=None):
        """Print usage information."""
        progName = os.path.basename(sys.argv[0])
        if errorMsg:
            print '%s: error: %s' % (progName, errorMsg)
        print 'Usage: %s --db DBNAME --model FILENAME' % progName
        print '       %s -h | --help' % progName
        print
        print 'Options:'
        print '    --prompt-for-args Prompt for args to use for initializing store (i.e. password)'
        print '    --show-progress   Print a dot on stderr as each class is processed'
        print '                      (useful when dumping large databases)'
        print
        print '       * DBNAME can be: %s' % ', '.join(self.databases())
        print
        sys.exit(1)

    def options(self, args):
        """Get command line options."""
        # Command line dissection
        if isinstance(args, basestring):
            args = args.split()
        optPairs, files = getopt(args[1:], 'h', ['help',
            'show-progress', 'db=', 'model=', 'outfile=', 'prompt-for-args'])
        if len(optPairs) < 1:
            self.usage('Missing options.')
        if len(files) > 0:
            self.usage('Extra files or options passed.')

        # Turn the cmd line optPairs into a dictionary
        opt = {}
        for key, value in optPairs:
            if key.startswith('--'):
                key = key[2:]
            elif key.startswith('-'):
                key = key[1:]
            opt[key] = value

        # Check for required opt, set defaults, etc.
        if 'h' in opt or 'help' in opt:
            self.usage()
        if 'db' not in opt:
            self.usage('No database specified.')
        if 'model' not in opt:
            self.usage('No model specified.')
        return opt


if __name__ == '__main__':
    Dump().main(sys.argv)
