#!/usr/bin/env python

"""Helper for cutting Python releases.

This script creates a compressed tar file named Webware-VER.tar.gz
in the parent directory of Webware. The package can be built either
from the current Git workspace or from a tag in the Git repository.

The current Git workspace will be used if you call the script without
any arguments, like that:

  > bin/ReleaseHelper.py

Since the release will be created from the files in the live workspace,
it should be clean and up to date and not have had install.py run on it,
or your distro will end up with generated docs. However, the versions
should have been set with the bin/setversion script.

The workspace will not be touched in the process.

The version number for the release tarball is taken from
Webware/Properties.py like you would expect.

Instead of using the workspace, you can also extract the release directly
from a tag in the Git repository, for instance:

  > bin/ReleaseHelper.py tag=1.1.2

This will extract the files tagged with 1.1.2 and build the
tarball Webware-1.1.2.tar.gz in Webware's parent directory.

This means the release will match exactly what is in the repository,
reducing the risk of local changes, modified files, or new files
which are not in the repository from showing up in the release.

This script only works on Posix. Releases are not created on Windows
because permissions and EOLs can be problematic for other platforms.
Use the option pgk=zip to create a zip archive instead of a tarball.

For more information, see the Release Procedures in the Webware docs.
"""

import os
import sys
import time


class ReleaseHelper(object):

    def main(self):
        self.writeHello()
        self.checkPlatform()
        self.readArgs()
        self.buildRelease()

    def buildRelease(self):
        """Prepare a release by extracting files from the repository.

        You can specify a tag name on the command line, like

          > bin/ReleaseHelper.py tag=1.1.2

        This will extract the files tagged with 1.1.2 and build the
        tarball Webware-1.1.2.tar.gz in your parent directory.

        This means the release will match exactly what is in the repository,
        and reduces the risk of local changes, modified files, or new
        files which are not in the repository from showing up in the release.
        """

        tag = self._args.get('tag')
        pkg = self._args.get('pkg')
        pkgType = 'zip archive' if pkg == 'zip' else 'tarball'
        if tag:
            print "Creating %s from tag %s ..." % (pkgType, tag)
        else:
            print "Creating %s from current workspace..." % pkgType

        # the location of this script:
        progPath = os.path.join(os.getcwd(), sys.argv[0])
        # we assume this script is located in Webware/bin/
        webwarePath = os.path.dirname(os.path.dirname(progPath))
        # make the Webware directory our current directory
        self.chdir(webwarePath)
        # the tarball will land in its parent directory:
        tarDir = os.pardir

        if webwarePath not in sys.path:
            sys.path.insert(1, webwarePath)
        from MiscUtils.PropertiesObject import PropertiesObject

        target = 'Release'
        try:
            os.mkdir(target)
        except OSError:
            print "Staging directory already exists:", target
            print "Please remove this directory."
            return

        cleanup = [target]

        source = 'tags/%s' % tag if tag else 'HEAD'

        try:
            self.run('git archive %s | tar -x -C %s' % (source, target))
            if not os.path.exists(target):
                print "Unable to extract from %r" % source
                if tag:
                    print "Perhaps the tag %r does not exist." % tag
                self.error()
            propertiesFile = os.path.join(target, 'Properties.py')
            if not os.path.exists(propertiesFile):
                self.error('Properties.py not found.')
            props = PropertiesObject(propertiesFile)
            if props.get('name') != 'Webware for Python':
                self.error('This is not a Webware package.')
            ver = props['versionString']

            print "Webware version is:", ver

            if not tag:
                # timestamp for time of release used to in versioning the file
                year, month, day = time.localtime(time.time())[:3]
                datestamp = "%04d%02d%02d" % (year, month, day)
                # drop leading 2 digits from year. (Ok, itn's not Y2K but it
                # is short and unique in a narrow time range of 100 years.)
                datestamp = datestamp[2:]
                ver += "-" + datestamp
                print "Packaged release will be:", ver

            pkgDir = "Webware-%s" % ver

            if os.path.exists(pkgDir):
                self.error("%s is in the way, please remove it." % pkgDir)

            # rename the target to the pkgDir so the extracted parent
            # directory from the tarball will be unique to this package.
            self.run("mv %s %s" % (target, pkgDir))

            cleanup.append(pkgDir)

            pkgExt = '.zip' if pkg == 'zip' else '.tar.gz'
            pkgName = os.path.join(pkgDir + pkgExt)

            # cleanup .git files
            self.run("find %s -name '.git*' -exec rm {} \;" % pkgDir)

            # We could cleanup any other files not part of this release here.
            # (For instance, we could create releases without documentation).

            # We could also create additional files to be part of this release
            # without being part of the repository, for instance documentation
            # that is automatically created from markup.

            pkgPath = os.path.join(tarDir, pkgName)

            if os.path.exists(pkgPath):
                self.error("%s is in the way, please remove it." % pkgPath)

            tarCmd = 'zip -qr' if pkg == 'zip' else 'tar -czf'
            self.run('%s %s %s' % (tarCmd, pkgPath, pkgDir))

            if not os.path.exists(pkgPath):
                self.error('Could not create %s.' % pkgType)

        finally:  # Clean up
            for path in cleanup:
                if os.path.exists(path):
                    self.run('rm -rf ' + path)

        print
        print "file:", pkgName
        print "dir:", os.path.abspath(tarDir)
        print "size:", os.path.getsize(pkgPath), 'Bytes'
        print
        print 'Success.'
        print

    def writeHello(self):
        print
        print 'Webware for Python'
        print 'Release Helper'
        print

    def checkPlatform(self):
        if os.name != 'posix':
            print 'This script only runs on Posix. Your op sys is %s.' % os.name
            print 'Webware releases are always created on Posix machines.'
            print 'These releases work on both Posix and MS Windows.'
            self.error()

    def readArgs(self):
        args = {}
        for arg in sys.argv[1:]:
            try:
                name, value = arg.split('=', 1)
            except ValueError:
                self.error('Invalid argument: %s' % arg)
            args[name] = value
        self._args = args

    def error(self, msg=''):
        if msg:
            print 'ERROR: %s' % msg
        sys.exit(1)

    def chdir(self, path):
        print 'cmd> chdir %s' % path
        os.chdir(path)

    def run(self, cmd):
        """Runs an arbitrary Unix command."""
        print 'cmd>', cmd
        results = os.popen(cmd).read()
        if results:
            print results


if __name__ == '__main__':
    ReleaseHelper().main()
