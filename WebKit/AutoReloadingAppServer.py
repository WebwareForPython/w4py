#!/usr/bin/env python

"""AutoReloadingAppServer

This module defines `AutoReloadingAppServer`, a replacement for `AppServer`
that adds a file-monitoring and restarting to the AppServer. Used mostly like:

    from AutoReloadingAppServer import AutoReloadingAppServer as AppServer

If `UseImportSpy` is set to False in AppServer.config, or FAM support is
not available, this requires regular polling. The interval for the polling
in seconds can be set with `AutoReloadPollInterval` in AppServer.config.
"""

import os
import sys
import errno
import select
from time import sleep
from threading import Thread

from AppServer import AppServer


defaultConfig = dict(
    AutoReload = False,
    AutoReloadPollInterval = 1,  # in seconds
    UseImportSpy = True,
    UseFAMModules = 'pyinotify gamin _fam')


def getFAM(modules):
    """Get FAM object based on the modules specified.

    Currently supported are
    pyinotify: http://github.com/seb-m/pyinotify
    python-gamin (gamin): http://www.gnome.org/~veillard/gamin/
    python-fam (_fam): http://python-fam.sourceforge.net
    """
    global fam

    for module in modules:

        try:
            fam = __import__(module)
        except ImportError:
            fam = None
        except Exception as e:
            print "Error loading %s: %s" % (module, str(e))
            fam = None
        if not fam:
            continue

        if hasattr(fam, 'WatchManager') and hasattr(
                fam, 'Notifier') and hasattr(fam, 'IN_MODIFY'):


            class FAM(object):
                """Simple File Alteration Monitor based on pyinotify"""

                @staticmethod
                def name():
                    return "pyinotify"

                def __init__(self):
                    """Initialize and start monitoring."""
                    self._wm = fam.WatchManager()
                    self._mask = fam.IN_MODIFY | fam.IN_CREATE
                    self._notifier = fam.Notifier(
                        self._wm, self.callback, timeout=0)
                    self._files = set()
                    self._queue = []

                def close(self):
                    """Stop monitoring and close."""
                    self._files = set()
                    self._notifier.stop()

                def fd(self):
                    """Get file descriptor for monitor."""
                    return self._wm.get_fd()

                def monitorFile(self, filepath):
                    """Monitor one file."""
                    if filepath not in self._files:
                        self._wm.add_watch(filepath, self._mask)
                        self._files.add(filepath)

                def pending(self):
                    """Check whether an event is pending."""
                    if not self._queue:
                        if self._notifier.check_events():
                            self._notifier.read_events()
                        self._notifier.process_events()
                    return self._queue

                def nextFile(self):
                    """Get next file and return whether it has changed."""
                    return self._queue.pop(0)

                def callback(self, event):
                    """Callback function for the Notifier."""
                    self._queue.append(({fam.IN_MODIFY: 'changed',
                        fam.IN_CREATE: 'created',
                        fam.IN_MOVE_SELF: 'moved',
                        fam.IN_DELETE_SELF: 'deleted',
                        fam.IN_IGNORED: 'changed'}.get(event.mask),
                        event.pathname))


        elif hasattr(fam, 'GAM_CONNECT') and hasattr(
                fam, 'WatchMonitor') and hasattr(fam, 'GAMChanged'):


            class FAM(object):
                """Simple File Alteration Monitor based on python-gamin"""

                @staticmethod
                def name():
                    return "python-gamin"

                def __init__(self):
                    """Initialize and start monitoring."""
                    self._mon = fam.WatchMonitor()
                    self._watchlist = []
                    self._files = set()

                def close(self):
                    """Stop monitoring and close."""
                    watchlist = self._watchlist
                    while watchlist:
                        self._mon.stop_watch(watchlist.pop())
                    self._files = set()
                    self._mon.disconnect()

                def fd(self):
                    """Get file descriptor for monitor."""
                    return self._mon.get_fd()

                def monitorFile(self, filepath):
                    """Monitor one file."""
                    if filepath not in self._files:
                        self._mon.watch_file(filepath, self.callback)
                        self._watchlist.append(filepath)
                        self._files.add(filepath)

                def pending(self):
                    """Check whether an event is pending."""
                    return self._mon.event_pending()

                def nextFile(self):
                    """Get next file and return whether it has changed."""
                    self._mon.handle_one_event()
                    return self._changed, self._filepath

                def callback(self, filepath, event):
                    """Callback function for WatchMonitor."""
                    self._filepath = filepath
                    self._changed = {fam.GAMChanged: 'changed',
                        fam.GAMCreated: 'created', fam.GAMMoved: 'moved',
                        fam.GAMDeleted: 'deleted'}.get(event)

        elif hasattr(fam, 'FAMConnection') and hasattr(
                fam, 'open') and hasattr(fam, 'Changed'):


            class FAM(object):
                """Simple File Alteration Monitor based on python-fam"""

                @staticmethod
                def name():
                    return "python-fam"

                def __init__(self):
                    """Initialize and start monitoring."""
                    self._fc = fam.open()
                    self._requests = []
                    self._files = set()

                def close(self):
                    """Stop monitoring and close."""
                    requests = self._requests
                    while requests:
                        requests.pop().cancelMonitor()
                    self._files = set()
                    self._fc.close()

                def fd(self):
                    """Get file descriptor for monitor."""
                    return self._fc

                def monitorFile(self, filepath):
                    """Monitor one file."""
                    if filepath not in self._files:
                        self._requests.append(
                                self._fc.monitorFile(filepath, None))
                        self._files.add(filepath)

                def pending(self):
                    """Check whether an event is pending."""
                    return self._fc.pending()

                def nextFile(self):
                    """Get next file and return whether it has changed."""
                    event = self._fc.nextEvent()
                    # we can also use event.code2str() here,
                    # but then we need to filter the events
                    changed = {fam.Changed: 'changed',
                        fam.Created: 'created', fam.Moved: 'moved',
                        fam.Deleted: 'deleted'}.get(event.code)
                    return changed, event.filename

        else:
            FAM = None

        if FAM:
            try:
                return FAM()
            except Exception as e:
                print "Error starting %s: %s" % (FAM.name(), str(e))
            FAM = None
        fam = None


class AutoReloadingAppServer(AppServer):
    """AppServer AutoReloading.

    This class adds functionality to `AppServer`, to notice changes to
    source files, including servlets, PSPs, templates or changes to the
    Webware source file themselves, and reload the server as necessary
    to pick up the changes.

    The server will also be restarted if a file which Webware *tried*
    to import is modified. This is so that changes to a file containing
    a syntax error (which would have prevented it from being imported)
    will also cause the server to restart.
    """


    ## Init ##

    def __init__(self, path=None):
        """Activate AutoReloading."""
        self._shouldRestart = False
        self._fileMonitorThread = None
        AppServer.__init__(self, path)
        try:
            if self.isPersistent() and self.setting('AutoReload'):
                self.activateAutoReload()
        except:
            AppServer.initiateShutdown(self)
            raise

    def defaultConfig(self):
        """Return the default configuration."""
        conf = AppServer.defaultConfig(self)
        # Update with AutoReloadingAppServer specific settings
        # as defined in defaultConfig on the module level:
        conf.update(defaultConfig)
        return conf

    def shutDown(self):
        """Shut down the monitoring thread.

        This is done in addition to the normal shutdown procedure.
        """
        self.deactivateAutoReload()
        AppServer.shutDown(self)


    ## Activation of AutoReload ##

    def activateAutoReload(self):
        """Start the monitor thread."""
        if self.setting('UseImportSpy'):
            self._imp.activateImportSpy()
            print 'ImportSpy activated.'
        if not self._fileMonitorThread:
            famModules = self.setting('UseFAMModules')
            try:
                famModules = famModules.split()
            except AttributeError:
                pass
            if famModules and self._imp._spy:
                # FAM will be only used when ImportSpy has been activated,
                # since otherwise we need to poll the modules anyway.
                try:
                    self._fam = getFAM(famModules)
                    self._pipe = None
                except Exception as e:
                    print "Error loading FAM: %s" % str(e)
                    self._fam = None
                if not self._fam:
                    print 'FAM not available, fall back to polling.'
            else:
                self._fam = None
            print 'AutoReload Monitor started,',
            if self._fam:
                self._pollInterval = 0
                print 'using %s.' % self._fam.name()
                target = self.fileMonitorThreadLoopFAM
            else:
                self._pollInterval = self.setting('AutoReloadPollInterval')
                print 'polling every %d seconds.' % self._pollInterval
                target = self.fileMonitorThreadLoop
            self._runFileMonitor = True
            self._fileMonitorThread = t = Thread(target=target)
            t.setName('AutoReloadMonitor')
            t.setDaemon(True)
            t.start()

    def deactivateAutoReload(self):
        """Stop the monitor thread."""
        if self._fileMonitorThread:
            print 'Stopping AutoReload Monitor...'
            if self._runFileMonitor:
                self._runFileMonitor = False
                if self._fam:
                    if self._pipe:
                        # Send a message down the pipe to wake up
                        # the monitor thread and tell him to quit:
                        os.write(self._pipe[1], 'stop')
                        os.close(self._pipe[1])
            sys.stdout.flush()
            if self._fileMonitorThread.isAlive():
                try:
                    self._fileMonitorThread.join(
                        max(3, 1.5 * self._pollInterval))
                    if self._fileMonitorThread.isAlive():
                        raise RuntimeError
                except Exception:
                    print 'Could not stop the AutoReload Monitor thread.'
            if self._fam:
                if self._pipe:
                    os.close(self._pipe[0])
                    self._pipe = None
                self._fam.close()
                self._fam = None


    ## Restart methods ##

    def restartIfNecessary(self):
        """Check if the app server should be restarted.

        This should be called regularly to see if a restart is required.
        The server can only restart from the main thread, other threads
        can't do the restart. So this polls to see if `shouldRestart`
        has been called.
        """
        if self._shouldRestart:
            self.restart()

    @staticmethod
    def restart():
        """Do the actual restart.

        Call `shouldRestart` from outside the class.
        """
        sys.stdout.flush()
        sys.stderr.flush()
        # calling execve() is problematic, since the file
        # descriptors don't get closed by the OS.  This can
        # result in leaked database connections.  Instead, we
        # exit with a special return code which is recognized
        # by the AppServer script, which will restart us upon
        # receiving that code.
        sys.exit(3)

    def monitorNewModule(self, filepath, mtime=None):
        """Add new file to be monitored.

        This is a callback which ImportSpy invokes to notify us of new files
        to monitor. This is only used when we are using FAM.
        """
        self._fam.monitorFile(os.path.abspath(filepath))


    ## Internal methods ##

    def shouldRestart(self):
        """Tell the main thread to restart the server."""
        self._shouldRestart = True
        self._runFileMonitor = False

    def fileMonitorThreadLoop(self):
        """This the the main loop for the monitoring thread.

        Runs in its own thread, polling the files for changes directly
        (i.e., going through every file that's being used and checking
        its last-modified time, seeing if it's been changed since it
        was initially loaded).
        """
        while self._runFileMonitor:
            sleep(self._pollInterval)
            f = self._imp.updatedFile()
            if f:
                print '*** The file', f, 'has changed.'
                print 'Restarting AppServer...'
                self.shouldRestart()

    def fileMonitorThreadLoopFAM(self):
        """Monitoring thread loop, but using the FAM library."""
        # For all of the modules which have _already_ been loaded,
        # we check to see if they've already been modified:
        f = self._imp.updatedFile()
        if f:
            print '*** The file', f, 'has changed.'
            print 'Restarting AppServer...'
            self.shouldRestart()
            return
        files = self._imp.fileList().keys()
        # Monitor all modules which will be loaded from now on
        self._imp.notifyOfNewFiles(self.monitorNewModule)
        # Monitor all modules which have already been loaded
        for f in files:  # note that files cannot change during this loop
            self.monitorNewModule(f)
        # Create a pipe so that this thread can be notified when the
        # server is shutdown. We use a pipe because it needs to be an object
        # which will wake up the call to 'select':
        self._pipe = os.pipe()
        fds = [self._fam.fd(), self._pipe[0]], [], []
        while self._runFileMonitor:
            try:
                # We block here until a file has been changed, or until
                # we receive word that we should shutdown (via the pipe).
                select.select(*fds)
            except select.error as e:
                if not self._runFileMonitor:
                    break
                if e[0] == errno.EINTR:
                    continue
                else:
                    print "Error:", e[1]
                    sys.exit(1)
            while self._runFileMonitor and self._fam.pending():
                c, f = self._fam.nextFile()
                if c and self._imp.fileUpdated(f):
                    print '*** The file %s has been %s.' % (f, c)
                    print 'Restarting AppServer...'
                    self.shouldRestart()
        self._imp.notifyOfNewFiles(None)
