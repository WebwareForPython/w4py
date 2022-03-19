#!/usr/bin/env python2

"""Set version.

This script updates the version number information
in the Properties.py files, as well as *.html and *.txt.

This should be used only by Webware developers whenever
a new Webware version is being cut. Please be very
careful and read also the ReleaseProcedures.html.

If setVersion is True, then the version information is updated
in various files as follows:

    Properties.py files version information is set, replacing the
    version setting and releaseDate setting.

    *.html files version information is set by searching for a
    comment tag surrounding both version and release date and replacing
    the version and release date information respectively.

    *.txt files version is set by matching
        :Version:
        :Released:
    tags at the beginning of the line. This is designed for the
    reStructured text documents. Note that reStructured text
    HTML files will need to be re-generated after processing.

    The version in ReleaseNotes-X.Y.phtml is not set (this will be
    done by the installer), but they are renamed to the current version.
    If possible, this is done with "git mv". Exception: If no new notes
    have been written (i.e. ReleaseNotes-X.Y same as ReleaseNotesTemplate),
    they will not be saved, but deleted, if possible, using "git rm".

If newRelease is True, then a new release is prepared as follows:

    The version in ReleaseNotes-X.Y.phtml files is set, and they
    are renamed to the current version if they are not empty.

    New ReleaseNotes-X.y.phtml files are created from the
    ReleaseNotesTemplates.phtml files instead.

    If possible, "git mv" and "git add" will be used.

Note that this script will not automatically perform a "git commit"
so you can always revert when something goes wrong.

You should not use "setVersion" on the master branch, but after creating
a tag for the desired version which must not be a final release.
You should use "newRelease" on the trunk for the final version
when you want to freeze the release notes and switch to empty
release notes for the next release.

Written by Stuart Donaldson - stu at asyn.com.
Improved by Christoph Zwerschke - cito at online.de.
"""

# Version format is (Major, Minor, Sub, Alpha/Beta/etc)
# The Sub is optional, and if 0 is not returned.
# Examples: (0, 8, 1, 'b1'), (0, 8, 2) or (0, 9, 0, 'rc1')
# releaseDate format should be 'MM/DD/YY'.

# Update this to change the current version and release date:
version = (1, 2, 4)
releaseDate = '03/19/22'

# Set Version info in files (should not be done on the trunk):
setVersion = True
# Prepare a new release (this should be done on the trunk):
newRelease = False

# Verbose output (output unchanged files also):
verbose = False

import os
import sys
import re
from glob import glob

# We assume that this script is located in Webware/bin:
progPath = os.path.abspath(sys.argv[0])
webwarePath = os.path.dirname(os.path.dirname(progPath))
sys.path.append(webwarePath)
os.chdir(webwarePath)

from MiscUtils.PropertiesObject import PropertiesObject


class Replacer(object):
    """Class to handle substitutions in a file."""

    def __init__(self, *args):
        self._subs = list(args)

    def add(self, search, replace):
        self._subs.append((re.compile(search, re.M), replace))

    def replaceInStr(self, data):
        for search, replace in self._subs:
            data = re.sub(search, replace, data)
        return data

    def replaceInFile(self, filename):
        data = open(filename, 'rb').read()
        newData = self.replaceInStr(data)
        if data == newData:
            if verbose:
                print 'Unchanged ' + filename
        else:
            print 'Updating ' + filename
            open(filename, 'wb').write(newData)
            if os.system('git add ' + filename):
                print "git add not possible."

    def replaceGlob(self, pattern):
        for filename in glob(pattern):
            if os.path.exists(filename):
                self.replaceInFile(filename)


def main():
    po = PropertiesObject()
    po.loadValues(version=version, releaseDate=releaseDate)
    po.createVersionString()

    if po['versionString'] == 'X.Y':
        print "Please set the version."
        sys.exit(1)
    elif po['releaseDate'] == '@@/@@/@@':
        print "Please set the release Date."
        sys.exit(1)

    propReplace = Replacer()
    propReplace.add(r"(version\s*=)\s*.*",  r"\g<1> %s" % repr(version))
    propReplace.add(r"(releaseDate\s*=)\s*.*", r"\g<1> %s" % repr(releaseDate))

    htmlReplace = Replacer()
    htmlReplace.add(r"<!--\s*version\s*-->[^<]*<!--\s*/version\s*-->",
        r"<!-- version --> %s <!-- /version -->" % po['versionString'])
    htmlReplace.add(r"<!--\s*relDate\s*-->[^<]*<!--\s*/relDate\s*-->",
        r"<!-- relDate --> %s <!-- /relDate -->" % po['releaseDate'])

    rstReplace = Replacer()
    rstReplace.add(r"^:Version:.*$", ":Version: %s" % po['versionString'])
    rstReplace.add(r"^:Released:.*$", ":Released: %s" % po['releaseDate'])

    phtmlReplace = Replacer()
    phtmlReplace.add(r"(<%.*)' \+ versionString \+ '(.*%>)",
        r"\g<1>%s\g<2>" % po['versionString'])
    phtmlReplace.add(r"<% versionString %>", po['versionString'])
    phtmlReplace.add(r"<% releaseDate %>", po['releaseDate'])

    twillReplace = Replacer()
    twillReplace.add(r"^setglobal version .*$",
        r"setglobal version %s" % po['versionString'])
    twillReplace.add(r"^setglobal date .*$",
        r"setglobal date %s" % po['releaseDate'])
    twillReplace.add(r"^# if release ", '')

    if setVersion:

        # Replace in Properties files:
        propReplace.replaceGlob('Properties.py')
        propReplace.replaceGlob('*/Properties.py')

        # Replace in existing HTML:
        htmlReplace.replaceGlob('*/Docs/*.html')
        htmlReplace.replaceGlob('Docs/*.html')

        # Replace in reStructuredText files:
        rstReplace.replaceGlob('*/Docs/*.txt')
        rstReplace.replaceGlob('Docs/*.txt')

        # Replace in global README file:
        rstReplace.replaceGlob('_README')

        # Replace in twill test scripts:
        twillReplace.replaceGlob('WebKit/Tests/twill/*.twill')

    # Process release notes:

    if setVersion or newRelease:
        template = open('DocSupport/RelNotesTemplate.phtml', 'rb').read()
        infile = 'RelNotes-X.Y.phtml'
        outfile = infile.replace('X.Y', po['versionString'])
        for filename in ['Docs/' + infile] + glob('*/Docs/' + infile):
            if verbose:
                print "Processing " + filename
            current = open(filename, 'rb').read()
            if current == template:
                if newRelease:
                    print "Kept empty " + filename
                    continue
                else:
                    print "Removing empty " + filename
                    if os.system('git rm ' + filename):
                        print "git rm not possible."
                        os.remove(filename)
            else:
                if newRelease:
                    phtmlReplace.replaceInFile(filename)
                newName = os.path.join(os.path.split(filename)[0], outfile)
                print "Renaming %s to %s" % (filename, outfile)
                if os.system('git mv -f %s %s' % (filename, newName)):
                    print "git mv not possible."
                    os.rename(filename, newName)
                if newRelease:
                    print "Creating empty " + filename
                    open(filename, 'wb').write(template)
                    if os.system('git add ' + filename):
                        print "git add not possible."


if __name__ == '__main__':
    main()
