#!/usr/bin/env python

"""checksrc.py


INTRODUCTION

This utility checks for violations of various source code conventions
in the hope of keeping the project clean and consistent.
Please see Webware/Documentation/StyleGuidelines.html for more information
including some guidelines not checked for by this utility.


COMMAND LINE

Running this program from the command line with -h will give you usage/help:
  > python checksrc.py -h

Examples:
  > python checksrc.py
  > python checksrc.py SomeDir
  > python checksrc.py -R SomeDir
  > python checksrc.py . results.text

And often you run it from the Webware directory like so:
  > cd Webware
  > python bin/checksrc.py


AS A MODULE AND CLASS

If you imported this as a module, you would use the CheckSrc class,
possibly like so:
    from CheckSrc import CheckSrc
    CheckSrc().check()

    # or:
    cs = CheckSrc()
    if cs.readArgs():
        cs.check()

    # or:
    cs = CheckSrc()
    cs.setOutput('results.text')
    cs.check()

And of course, you could subclass CheckSrc() to customize it,
which is why even command line utils get done with classes
(rather than collections of functions and nekkid code).

You can also setDirectory(), setOutput() setRecurse() and setVerbose()
the defaults of which are '.', sys.stdout, True and False.


CAVEATS

Note that checksrc.py takes a line oriented approach. Since it does not
actually properly parse Python code, it can be fooled in some cases.
Therefore, it's possible to get false alarms. However, most of these are
created by triple quoted strings which we remove before checking the file.
While we could implement a full parser to close the gap, doing so would be
labor intensive with little pay off. So we live with a few false alarms.


CONFIG FILES

You can modify the behavior of checksrc.py for a particular directory
by creating a .checksrc.config file like so:

{
    'SkipDirs': ['Cache'],
    'SkipFiles': ['fcgi.py', 'zCookieEngine.py'],
    'DisableErrors': {
        'UncapFN': '*',
        'ExtraUnder': ['MiddleObject'],
    }
}

Some notes:
  * You can specify some or all of the options.
  * SkipDirs and SkipFiles both require lists of filenames.
  * DisableError keys are error codes defined by checksrc.py.
    You can find these out by running checksrc with the
    -h command line option or checking the source below.
  * The value for disabling an error:
      * Can be an individual filename or a list of filenames.
      * Can be '*' for "all files".


RULES

  * File names start with capital letter.
  * (On POSIX) Files don't contain \r.
  * Four spaces are used for indentation.
  * Tabs are not used at all.
  * Class names start with a capital letter.
  * Method names start with a lower case letter.
  * Methods do not start with "get".
  * Data attributes start with an underscore _,
    and are followed by a lower case letter.
  * Method and attribute names have no underscores after the first character.
  * Expressions following if, while and return
    are not enclosed in parenthesees, ().
  * Class defs and category comments, ## Like this ##
    are preceded by 2 blank lines and are followed by one blank line
    (unless the class implementation is pass).


FUTURE

Consider (optionally) displaying the source line.

Maybe: Experiment with including the name of the last seen method/function
with the error messages to help guide the user to where the error occurred.

Consider using the parser or tokenize modules of the standard library.
"""

import re
import sys
import os


class NoDefault(object):
    """Singleton for parameters with no default."""


class CheckSrc(object):
    """The source checker."""


    ## Init ##

    _maxLineSize = 100

    _errors = {
        'UncapFN':
            'Uncapitalized filename.',
        'CarRet':
            'Carriage return \\r found.',
        'Tab':
            'Tab character \\t found.',
        'LineSize':
            'Limit line to a maximum of %d characters.' % _maxLineSize,
        'WrongIndent':
            'Four spaces should be used per indentation level.',
        'NoBlankLines':
            '%(what)s should be preceded by %(separator)s.',
        'ClassNotCap':
            'Class names should start with capital letters.',
        'MethCap':
            'Method name "%(name)s" should start with a lower case letter.',
        'GetMeth':
            'Method name "%(name)s" should not start with "get".',
        'NoUnderAttr':
            'Data attributes should start with an underscore: %(attribute)s.',
        'NoLowerAttr':
            'Data attributes should start with an underscore and then'
            ' a lower case letter: %(attribute)s.',
        'ExtraUnder':
            'Attributes and methods should not have underscores past'
            ' the first character: %(attribute)s.',
        'ExtraParens':
            'No outer parentheses should be used for "%(keyword)s".',
        'ObsExpr':
            '"%(old)s" is obsolescent, use "%(new)s" instead.',
        'OpNoSpace':
            'Operator "%(op)s" should be padded with one blank.',
        'CommaNoSpace':
            'Commas and semicolons should be followed by a blank.',
        'PaddedParens':
            'Parentheses should not be padded with blanks.',
        'NoCompStmts':
            'Compound statements are generally discouraged.',
        'AugmStmts':
            'Consider using augmented assignment "%(op)s."',
    }

    def __init__(self):
        # Grab our own copy of errors with lower case keys
        self._errors = {}
        self._errorCodes = []
        for key, value in self.__class__._errors.items():
            self._errorCodes.append(key)
            self._errors[key.lower()] = value

        # Misc init
        self._config = {}

        # Set default options
        self.setDirectory('.')
        self.setWithDir(False)
        self.setOutput(sys.stdout)
        self.setRecurse(True)
        self.setVerbose(False)


    ## Options ##

    def directory(self):
        return self._directory

    def setDirectory(self, dir):
        """Sets the directory that checking starts in."""
        self._directory = dir

    def withDir(self):
        return self._withDir

    def setWithDir(self, flag):
        """Set whether or not to print directories separately."""
        self._withDir = flag

    def output(self):
        return self._out

    def setOutput(self, output):
        """Set the destination output.

        It can either be an object which must respond to write() or
        a string which is a filename used for one invocation of check().
        """
        if isinstance(output, basestring):
            self._out = open(output, 'w')
            self._shouldClose = True
        else:
            self._out = output
            self._shouldClose = False

    def recurse(self):
        return self._recurse

    def setRecurse(self, flag):
        """Set whether or not to recurse into subdirectories."""
        self._recurse = flag

    def verbose(self):
        return self._verbose

    def setVerbose(self, flag):
        """Set whether or not to print extra information during check.

        For instance, print every directory and file name scanned.
        """
        self._verbose = flag


    ## Command line use ##

    def readArgs(self, args=sys.argv):
        """Read a list of arguments in command line style (e.g., sys.argv).

        You can pass your own args if you like, otherwise sys.argv is used.
        Returns True on success; False otherwise.
        """
        setDir = setOut = False
        for arg in args[1:]:
            if arg == '-h' or arg == '--help':
                self.usage()
                return False
            elif arg == '-d':
                self.setWithDir(True)
            elif arg == '-D':
                self.setWithDir(False)
            elif arg == '-r':
                self.setRecurse(True)
            elif arg == '-R':
                self.setRecurse(False)
            elif arg == '-v':
                self.setVerbose(True)
            elif arg == '-V':
                self.setVerbose(False)
            elif arg[0] == '-':
                self.usage()
                return False
            else:
                if not setDir:
                    self.setDirectory(arg)
                    setDir = True
                elif not setOut:
                    self.setOutput(arg)
                    setOut = True
                else:
                    self.write('Error: %s\n' % repr(arg))
                    self.usage()
                    return False
        return True

    def usage(self):
        progName = sys.argv[0]
        self.write('''Usage: %s [options] [startingDir [outputFilename]]

    -h --help = help
    -d -D = show dirs with files, show dirs separately (default -D)
    -r -R = recurse, do not recurse (default -r)
    -v -V = verbose, not verbose (default -V)

    Examples:
    > python checksrc.py
    > python checksrc.py SomeDir
    > python checksrc.py -R SomeDir
    > python checksrc.py . results.text

Error codes and their messages:
''' % progName)

        # Print a list of error codes and their messages
        keys = sorted(self._errorCodes)
        maxLen = 0
        for key in keys:
            if len(key) > maxLen:
                maxLen = len(key)
        for key in keys:
            paddedKey = key.ljust(maxLen)
            self.write('  %s = %s\n' % (paddedKey, self._errors[key.lower()]))
        self.write('\n.checksrc.config options include'
            ' SkipDirs, SkipFiles and DisableErrors.\n'
            'See the checksrc.py doc string for more info.\n')


    ## Printing, errors, etc. ##

    def write(self, *args):
        """Invoked by self for all printing.

        This allows output to be easily redirected.
        """
        write = self._out.write
        for arg in args:
            write(str(arg))

    def error(self, msgCode, args=NoDefault):
        """Invoked by self when a source code error is detected.

        Prints the error message and its location.
        Does not raise exceptions or halt the program.
        """
        # Implement the DisableErrors option
        disableNames = self.setting('DisableErrors', {}).get(msgCode, [])
        if ('*' in disableNames or self._fileName in disableNames
                or os.path.splitext(self._fileName)[0] in disableNames):
            return
        if not self._withDir and not self._printedDir:
            self.printDir()
        msg = self._errors[msgCode.lower()]
        if args is not NoDefault:
            msg %= args
        self.write(self.location(), msg, '\n')

    def fatalError(self, msg):
        """Report a fatal error and raise CheckSrcError.

        For instance, handle an invalid configuration file.
        """
        self.write('FATAL ERROR: %s\n' % msg)
        raise CheckSrcError

    def location(self):
        """Return a string indicating the current location.

        The string format is "fileName:lineNum:charNum:".
        The string may be shorter if the latter components are undefined.
        """
        s = ''
        if self._fileName is not None:
            if self._withDir:
                s += self._dirName + os.sep
            s += self._fileName
            if self._lineNum is not None:
                s += ':' + str(self._lineNum)
                if self._charNum is not None:
                    s += ':' + str(self._charNum)
        if s:
            s += ':'
        return s

    def printDir(self):
        """Self utility method to print the directory being processed."""
        self.write('\n', self._dirName, '\n')
        self._printedDir = True


    ## Configuration ##

    def readConfig(self, dirName):
        filename = os.path.join(dirName, '.checksrc.config')
        try:
            contents = open(filename).read()
        except IOError:
            return
        try:
            config = eval(contents)
        except Exception:
            self.fatalError('Invalid config file at %s.' % filename)
        # For DisableErrors, we expect a dictionary keyed by error codes.
        # For each code, we allow a value that is either a string or a list.
        # But for ease-of-use purposes, we now convert single strings to
        # lists containing the string.
        d = config.get('DisableErrors') or {}
        for key, value in d.items():
            if isinstance(value, basestring):
                d[key] = [value]
        self._config = config

    def setting(self, name, default=NoDefault):
        if default is NoDefault:
            return self._config[name]
        else:
            return self._config.get(name, default)


    ## Checking ##

    def check(self):
        if self._recurse:
            os.path.walk(self._directory, self.checkDir, None)
        else:
            self.checkDir(None, self._directory, os.listdir(self._directory))
        if self._shouldClose:
            self._out.close()

    def checkDir(self, arg, dirName, names):
        """Invoked by os.path.walk() which is kicked off by check().

        Recursively checks the given directory and all its subdirectories.
        """
        # Initialize location attributes.
        # These are updated while processing and
        # used when reporting errors.
        self._dirName = dirName
        self._fileName = None
        self._lineNum = None
        self._charNum = None
        self._printedDir = False

        if self._verbose:
            self.printDir()

        self.readConfig(dirName)

        # Prune directories based on configuration:
        skipDirs = self.setting('SkipDirs', [])
        for dir in skipDirs:
            try:
                names.remove(dir)
            except ValueError:
                pass
            else:
                print '>> skipping', dir

        skipFiles = self.setting('SkipFiles', [])
        for name in names:
            if (name.endswith('.py') and name not in skipFiles
                    and os.path.splitext(name)[0] not in skipFiles):
                try:
                    self.checkFile(dirName, name)
                except CheckSrcError:
                    pass

    _tripleQuotesRe = re.compile('""".*?"""'+ "|'''.*?'''", re.DOTALL)

    def removeTripeQuotedStrings(self, contents):
        return self._tripleQuotesRe.sub(
            lambda s: '"""%s"""' % ('\n' * s.group(0).count('\n')), contents)

    def checkFile(self, dirName, name):
        self._fileName = name
        if self._verbose:
            self.write('  %s\n' % self._fileName)

        self.checkFilename(name)

        filename = os.path.join(dirName, name)
        contents = open(filename, 'rb').read()
        self.checkFileContents(contents)

        contents = open(filename).read()
        lines = self.removeTripeQuotedStrings(contents).splitlines()
        self.checkFileLines(lines)

    def checkFilename(self, filename):
        if filename[0] != filename[0].upper():
            self.error('UncapFN')

    def checkFileContents(self, contents):
        if os.name == 'posix' and '\r' in contents:
            self.error('CarRet')

    def checkFileLines(self, lines):
        self._lineNum = 1
        self._blankLines = 2
        self._inMLS = None  # MLS = multi-line string
        for line in lines:
            self.checkFileLine(line)

    def checkFileLine(self, line):
        line = line.rstrip()
        if line:
            self.checkLineSize(line)
            line = self.clearStrings(line)
            if line:
                self.checkTabsAndSpaces(line)
                lineleft = line.lstrip()
                indent = line[:len(line) - len(lineleft)]
                line = lineleft
                parts = line.split()
                self.checkBlankLines(line, indent)
                self.checkCompStmts(parts, line)
                self.checkAugmStmts(parts)
                self.checkClassName(parts)
                self.checkMethodName(parts, indent)
                self.checkExtraParens(parts, line)
                self.checkPaddedParens(line)
                self.checkAttrNames(line)
                self.checkOperators(line)
                self.checkCommas(line)
                self._blankLines = 0
            else:
                self._blankLines = 1
        else:
            self._blankLines += 1
        self._lineNum += 1

    def checkLineSize(self, line):
        if len(line) > self._maxLineSize:
            self.error('LineSize')

    def clearStrings(self, line):
        """Return line with all quoted strings cleared."""
        pos = 0
        quote = self._inMLS
        while pos >= 0:
            if quote:
                pos2 = pos
                while 1:
                    pos2 = line.find(quote, pos2)
                    if pos2 > 0 and line[pos2 - 1] == '\\':
                        pos2 += 1
                        continue
                    break
                if pos2 >= 0:
                    if pos < len(line):
                        line = line[:pos] + '...'
                    break
                if pos < pos2:
                    line = line[:pos] + '...' + line[pos2:]
                    pos += 3
                pos += len(quote)
                quote = None
            pos3 = line.find('#', pos)
            pos2 = line.find("'", pos)
            pos = line.find('"', pos)
            if pos2 >= 0 and (pos == -1 or pos2 < pos):
                pos = pos2
            if pos3 >= 0 and (pos == -1 or pos3 < pos):
                if (line[pos3+1:pos3+2] == '#'
                        and not line[:pos3].rstrip()):
                    # keep category comments
                    line = line[:pos3+2]
                else:
                    # remove any other comment
                    line = line[:pos3].rstrip()
                break
            if pos >= 0:
                quote = line[pos]
                if line[pos:pos+3] == quote*3:
                    quote *= 3
                pos += len(quote)
        if quote and len(quote) < 3:
            quote = None
        self._inMLS = quote
        return line

    def checkBlankLines(self, line, indent):
        blankLines = self._blankLines
        minLines = 1 - len(indent)/4
        if line.startswith('##') and blankLines < minLines + 1:
            what = 'Category comments'
            separator = 'two blank lines'
        elif (line.startswith('class ') and blankLines < minLines + 1
                and not line.endswith(('Exception):', 'Error):', 'pass'))):
            what = 'Class definitions'
            separator = 'two blank lines'
        elif (line.startswith('def ') and blankLines < minLines
                and not line.endswith('pass')):
            what = 'Function definitions'
            separator = 'one blank line'
        else:
            return
        self.error('NoBlankLines', locals())

    def checkTabsAndSpaces(self, line):
        if '\t' in line:
            self.error('Tab')
            line = line.replace('\t', '    ')
        indent = len(line) - len(line.lstrip())
        if indent % 4:
            self.error('WrongIndent')

    def checkClassName(self, parts):
        if 'class' in parts:  # e.g. if 'class' is a standalone word
            if parts[0] == 'class':  # e.g. if start of the line
                name = parts[1]
                if name and name[0] != name[0].upper():
                    self.error('ClassNotCap')

    def checkMethodName(self, parts, indent):
        if 'def' in parts:  # e.g. if 'def' is a standalone word
            if parts[0] == 'def' and indent:
                # e.g. if start of the line, and indented
                # (indicating method and not function)
                name = parts[1]
                name = name[:name.find('(')]
                if name and name[0] != name[0].lower():
                    self.error('MethCap', locals())
                if len(name) > 3 and name[:3].lower() == 'get':
                    self.error('GetMeth', locals())

    _exprKeywords = set('assert for if return while with yield'.split())

    def checkExtraParens(self, parts, line):
        if (len(parts) > 1 and parts[0] in self._exprKeywords
                and parts[1].startswith('(')
                and parts[-1].replace(':', '').rstrip().endswith(')')
                and not line.count(')') < line.count('(')):
            keyword = parts[0]
            self.error('ExtraParens', locals())

    _blockKeywords = set('if elif else: try: except: while for with'.split())

    def checkCompStmts(self, parts, line):
        if (len(parts) > 1 and parts[0] in self._blockKeywords
                and ': ' in line and not line.endswith(':')):
            self.error('NoCompStmts')
        else:
            pos = line.find(';')
            if pos >= 0 and line.find('"') < pos and line.find("'") < pos:
                self.error('NoCompStmts')

    # Any kind of access of self
    _accessRE = re.compile(r'self\.(\w+)\s*(\(?)')
    # Irregular but allowed attribute names
    _allowedAttrNames = set(('assert_', 'has_key'))

    def checkAttrNames(self, line):
        for match in self._accessRE.findall(line):
            attribute = match[0]
            isMethod = match[1] == '('
            if not isMethod:
                if not attribute[0] == '_':
                    # Attribute names that are data (and not methods)
                    # should start with an underscore.
                    self.error('NoUnderAttr', locals())
                elif not (attribute.endswith('__') or attribute[1:2].islower()):
                    # The underscore should be followed by a lower case letter.
                    self.error('NoLowerAttr', locals())
            # Attribute names should have no underscores after the first one.
            if len(attribute) > 2 and attribute.startswith('__'):
                inner = attribute[2:]
                if inner.endswith('__'):
                    inner = inner[:-2]
            else:
                if len(attribute) > 1 and attribute.startswith('_'):
                    inner = attribute[1:]
                else:
                    inner = attribute
            if '_' in inner and not inner in self._allowedAttrNames:
                self.error('ExtraUnder', locals())

    # Assignment operators and augmented assignments
    _assignRE = re.compile(
        r'[^<>!=\s](\s*)(\+|\-|\*|/|//|%|\*\*|>>|<<|&|\^|\|)?=(\s*)[^=\s]')
    # Comparison Operators
    _compareRE = re.compile(
        r'[^<>!=\'\"\s](\s*)(<|>|==|>=|<=|<>|!=)(\s*)[^<>=\s]')

    def checkOperators(self, line):
        if '<>' in line:
            self.error('ObsExpr', {'old': '<>', 'new': '!='})
        for match in self._assignRE.findall(line):
            if not match[0] and not match[1] and not match[2]:
                continue  # allow this style for keyword arguments
            if match[0] != ' ' or match[2] != ' ':
                self.error('OpNoSpace', {'op': match[1] + '='})
        for match in self._compareRE.findall(line):
            if match[0] != ' ' or match[2] != ' ':
                self.error('OpNoSpace', {'op': match[1]})

    # Augmented assignment operators
    _augmOp = set('+ - * / % ** >> << & ^ |'.split())

    def checkAugmStmts(self, parts):
        if (len(parts) > 4 and parts[1] == '='
                and parts[0] == parts[2] and parts[3] in self._augmOp):
            self.error('AugmStmts', {'op': parts[3] + '='})

    # Commas and semicolons not followed by a blank
    _commaRE = re.compile('(,|;)[^\s\)]')

    def checkCommas(self, line):
        if self._commaRE.search(line):
            self.error('CommaNoSpace')

    # Parens padded with blanks
    _parensRE = re.compile('[(\(\{\[]\s+|\s+[\)\}\]]')

    def checkPaddedParens(self, line):
        if self._parensRE.search(line):
            self.error('PaddedParens')


class CheckSrcError(Exception):
    """Source check error."""


class _DummyWriter(object):
    """Dummy writer ignoring everything written."""

    def write(self, msg):
        pass


if __name__ == '__main__':
    checkSrc = CheckSrc()
    if checkSrc.readArgs():
        checkSrc.check()
