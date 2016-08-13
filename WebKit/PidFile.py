"""Process id file management"""

import os
import atexit

if os.name == 'nt':
    try:
        import win32api
    except ImportError:
        try:
            import ctypes
            win32api = ctypes.windll.kernel32
        except (AttributeError, ImportError):
            win32api = None
else:
    win32api = None


class ProcessRunning(Exception):
    """Error when creating pid file for already running process."""


class PidFile(object):
    """Process id file management."""

    def __init__(self, path, create=True):
        """Create a pid file with the given path for the current process."""
        self._path = path
        self._created = False
        self._pid = None
        if os.path.exists(path):
            try:
                self._pid = int(open(path).read())
                if self._pid <= 1:
                    self._pid = None
                    raise ValueError
            except (IOError, ValueError, TypeError):
                # Can't open file or read PID from file.
                # File is probably  invalid or stale, so try to delete it.
                print ("%s is invalid or cannot be opened;"
                    " attempting to remove it." % path)
                self.remove(stale=True)
            else:
                if self.pidRunning(self._pid):
                    if create:
                        raise ProcessRunning()
                else:
                    print "%s is stale; removing." % path
                    self.remove(stale=True)
        if create:
            self._pid = self.currentPID()
            if self._pid is not None:
                self.write()
                # Delete the pid file when Python exits, so that the pid file
                # is removed if the process exits abnormally. If the process
                # crashes, though, the pid file will be left behind.
                atexit.register(self.remove)

    @staticmethod
    def pidRunning(pid):
        """Check whether process with given pid is running."""
        try:
            os.kill(pid, 0)
        except OSError as e:
            if e.errno == 3:  # no such process
                return False
        except AttributeError:
            if win32api:
                try:
                    if not win32api.OpenProcess(1024, False, pid):
                        return False
                except win32api.error as e:
                    if e.winerror == 87:  # wrong parameter (no such process)
                        return False
        return True

    @staticmethod
    def currentPID():
        """Get the current process id."""
        try:
            return os.getpid()
        except AttributeError:
            if win32api:
                return win32api.GetCurrentProcessId()
        return None

    @staticmethod
    def killPID(pid, sig=None):
        """Kill the process with the given pid."""
        try:
            if sig is None:
                from signal import SIGTERM
                sig = SIGTERM
            os.kill(pid, sig)
        except (AttributeError, ImportError):
            if win32api:
                handle = win32api.OpenProcess(1, False, pid)
                win32api.TerminateProcess(handle, -1)
                win32api.CloseHandle(handle)

    def pid(self):
        """Return our process id."""
        return self._pid

    def running(self):
        """Check whether our process is running."""
        return self.pidRunning(self._pid)

    def kill(self):
        """Kill our process."""
        if self._pid is None:
            return
        return self.killPID(self._pid)

    def __del__(self):
        """Remove pid file together with our instance."""
        self.remove()

    def remove(self, stale=False):
        """Remove our pid file."""
        if not stale:
            if not self._created:
                # Only remove the file if we created it. Otherwise starting
                # a second process will remove the file created by the first.
                return
            stale = os.path.exists(self._path)
        if stale:
            try:
                os.unlink(self._path)
            except (AttributeError, OSError):
                pass
        self._created = False  # remove only once

    def write(self):
        """Write our pid file."""
        if self._created:
            return
        with open(self._path, 'w') as pidfile:
            pidfile.write(str(self._pid))
        self._created = True  # write only one
