"""This module defines a class for handling writing responses."""

debug = False


class InvalidCommandSequence(Exception):
    """Invalid command sequence error"""


class ConnectionAbortedError(Exception):
    """Connection aborted error"""


class ASStreamOut(object):
    """This is a response stream to the client.

    The key attributes of this class are:

    `_autoCommit`:
        If True, the stream will automatically start sending data
        once it has accumulated `_bufferSize` data. This means that
        it will ask the response to commit itself, without developer
        interaction. By default, this is set to False.
    `_bufferSize`:
        The size of the data buffer. This is only used when autocommit
        is True. If not using autocommit, the whole response is
        buffered and sent in one shot when the servlet is done.
    `flush()`:
        Send the accumulated response data now. Will ask the `Response`
        to commit if it hasn't already done so.
    """

    def __init__(self, autoCommit=False, bufferSize=8192):
        self._autoCommit = autoCommit
        self._bufferSize = bufferSize
        self._committed = False
        self._needCommit = False
        self._buffer = ''
        self._chunks = []
        self._chunkLen = 0
        self._closed = False

    def autoCommit(self):
        """Get the auto commit mode."""
        return self._autoCommit

    def setAutoCommit(self, autoCommit=True):
        """Set the auto commit mode."""
        self._autoCommit = bool(autoCommit)

    def bufferSize(self):
        """Get the buffer size."""
        return self._bufferSize

    def setBufferSize(self, bufferSize=8192):
        """Set the buffer size."""
        self._bufferSize = int(bufferSize)

    def flush(self):
        """Flush stream.

        Send available data as soon as possible, i.e. *now*.

        Returns True if we are ready to send, otherwise False (i.e.,
        if the buffer is full enough).
        """
        if self._closed:
            raise ConnectionAbortedError
        if debug:
            print ">>> Flushing ASStreamOut"
        if not self._committed:
            if self._autoCommit:
                if debug:
                    print "ASSTreamOut.flush setting needCommit"
                self._needCommit = True
            return False
        try:
            self._buffer += ''.join(self._chunks)
        finally:
            self._chunks = []
            self._chunkLen = 0
        return True

    def buffer(self):
        """Return accumulated data which has not yet been flushed.

        We want to be able to get at this data without having to call
        flush() first, so that we can (for example) integrate automatic
        HTML validation.
        """
        if self._buffer:  # if flush has been called, return what was flushed
            return self._buffer
        else:  # otherwise return the buffered chunks
            return ''.join(self._chunks)

    def clear(self):
        """Try to clear any accumulated response data.

        Will fail if the response is already committed.
        """
        if debug:
            print ">>> ASSTreamOut clear called"
        if self._committed:
            raise InvalidCommandSequence
        self._buffer = ''
        self._chunks = []
        self._chunkLen = 0

    def close(self):
        """Close this buffer. No more data may be sent."""
        if debug:
            print ">>> ASSTreamOut close called"
        self.flush()
        self._closed = True
        self._committed = True
        self._autocommit = True

    def closed(self):
        """Check whether we are closed to new data."""
        return self._closed

    def size(self):
        """Return the current size of the data held here."""
        return self._chunkLen + len(self._buffer)

    def prepend(self, charstr):
        """Add the attached string to the front of the response buffer.

        Invalid if we are already committed.
        """
        if self._committed or self._closed:
            raise InvalidCommandSequence
        if self._buffer:
            self._buffer = charstr + self._buffer
        else:
            self._chunks.insert(0, charstr)
            self._chunkLen += len(charstr)

    def pop(self, count):
        """Remove count bytes from the front of the buffer."""
        if debug:
            print "ASSTreamOut popping %s" % count
        self._buffer = self._buffer[count:]

    def committed(self):
        """Are we committed?"""
        return self._committed

    def needCommit(self):
        """Request for commitment.

        Called by the `HTTPResponse` instance that is using this instance
        to ask if the response needs to be prepared to be delivered.
        The response should then commit its headers, etc.
        """
        return self._needCommit

    def commit(self, autoCommit=True):
        """Called by the Response to tell us to go.

        If `_autoCommit` is True, then we will be placed into autoCommit mode.
        """
        if debug:
            print ">>> ASStreamOut Committing"
        self._committed = True
        self._autoCommit = autoCommit
        self.flush()

    def write(self, charstr):
        """Write a string to the buffer."""
        if debug:
            print ">>> ASStreamOut writing %s characters" % len(charstr)
        if self._closed:
            raise ConnectionAbortedError
        self._chunks.append(charstr)
        self._chunkLen += len(charstr)
        if self._autoCommit and self._chunkLen > self._bufferSize:
            if debug:
                print ">>> ASStreamOut.write flushing"
            self.flush()
