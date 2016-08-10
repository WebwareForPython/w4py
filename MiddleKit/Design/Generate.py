#!/usr/bin/env python

"""Generate.py

> python Generate.py -h
"""

import os
import sys
from getopt import getopt
import FixPath
import MiddleKit

if sys.platform == 'win32':
    # without this, I can't see output from uncaught exceptions!
    # perhaps this is caused by the recent incorporation of win32all (via DataTable)?
    sys.stderr = sys.stdout


class Generate(object):

    def databases(self):
        """Return a list with the names of the supported database engines."""
        return ['MSSQL', 'MySQL', 'PostgreSQL', 'SQLite']

    def main(self, args=sys.argv):
        """Main method."""
        opt = self.options(args)

        # Make or check the output directory
        outdir = opt['outdir']
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        elif not os.path.isdir(outdir):
            print 'Error: Output target, %s, is not a directory.' % outdir

        # Generate
        if 'sql' in opt:
            print 'Generating SQL...'
            self.generate(
                pyClass = opt['db'] + 'SQLGenerator',
                model = opt['model'],
                configFilename = opt.get('config'),
                outdir = os.path.join(outdir, 'GeneratedSQL'))
        if 'py' in opt:
            print 'Generating Python...'
            self.generate(
                pyClass = opt['db'] + 'PythonGenerator',
                model = opt['model'],
                configFilename = opt.get('config'),
                outdir=outdir)
        model = MiddleKit.Core.Model.Model(opt['model'],
            configFilename=opt.get('config'), havePythonClasses=0)
        model.printWarnings()

    def usage(self, errorMsg=None):
        """Print usage information."""
        progName = os.path.basename(sys.argv[0])
        if errorMsg:
            print '%s: error: %s' % (progName, errorMsg)
            print
        print '''\
Usage: %s --db DBNAME --model FILENAME \\
           [--sql] [--py] [--config FILENAME] [--outdir DIRNAME]
       %s -h | --help

    * Known databases include: %s.
    * If neither --sql nor --py are specified, both are generated.
    * If --outdir is not specified,
      then the base filename (sans extension) is used.
    * --config lets you specify a different config filename inside the model.
      This is mostly useful for the regression test suite.
'''  % (progName, progName, ', '.join(self.databases()))
        sys.exit(1)

    def options(self, args):
        """Get command line options."""
        # Command line dissection
        if isinstance(args, basestring):
            args = args.split()
        optPairs, files = getopt(args[1:], 'h',
            ['help', 'db=', 'model=', 'sql', 'py', 'config=', 'outdir='])
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
        if 'sql' not in opt and 'py' not in opt:
            opt['sql'] = ''
            opt['py'] = ''
        if 'outdir' not in opt:
            opt['outdir'] = os.curdir

        return opt

    def generate(self, pyClass, model, configFilename, outdir):
        """Generate code using the given class, model and output directory.

        The pyClass may be a string, in which case a module of the same name is
        imported and the class extracted from that. The model may be a string,
        in which case it is considered a filename of a model.
        """
        if isinstance(pyClass, basestring):
            module = __import__(pyClass, globals())
            pyClass = getattr(module, pyClass)
        generator = pyClass()
        if isinstance(model, basestring):
            generator.readModelFileNamed(model,
                configFilename=configFilename, havePythonClasses=False)
        else:
            generator.setModel(model)
        generator.generate(outdir)


if __name__ == '__main__':
    Generate().main(sys.argv)
