"""Per-thread list."""

import thread


class PerThreadList(object):
    """Per-thread list.

    PerThreadList behaves like a normal list, but changes to it are kept
    track of on a per-thread basis.  So if thread A appends an item to
    the list, only thread A sees that item.  There are a few non-standard
    methods (clear, isEmpty), too.

    This is implemented by keeping a dictionary of lists; one for each
    thread. The implementation is not a complete list wrapper; only some
    methods are implemented. If more methods are needed, see UserList
    (in the standard Python lib) for inspiration.
    """

    def __init__(self):
        self.data = {}

    def append(self, item, gettid=thread.get_ident):
        threadid = gettid()
        try:
            self.data[threadid].append(item)
        except KeyError:
            self.data[threadid] = [item]

    def extend(self, items, gettid=thread.get_ident):
        threadid = gettid()
        try:
            self.data[threadid].extend(items)
        except KeyError:
            self.data[threadid] = items

    def clear(self, allThreads=False, gettid=thread.get_ident):
        """Erases the list, either for the current thread or for all threads.

        We need this method, because it obviously won't work for user code
        to do: list = [].
        """
        if allThreads:
            self.data = {}
        else:
            threadid = gettid()
            try:
                self.data[threadid] = []
            except Exception:
                pass

    def items(self, allThreads=False, gettid=thread.get_ident):
        if allThreads:
            items = []
            for v in self.data.values():
                items.extend(v)
            return items
        else:
            threadid = gettid()
            try:
                return self.data[threadid]
            except KeyError:
                return []

    def isEmpty(self, gettid=thread.get_ident):
        """Test if the list is empty for all threads."""
        for v in self.data.values():
            if v:
                return False
        return True

    def __len__(self, gettid=thread.get_ident):
        threadid = gettid()
        try:
            return len(self.data[threadid])
        except KeyError:
            return 0

    def __getitem__(self,  i, gettid=thread.get_ident):
        threadid = gettid()
        if threadid in self.data:
            return self.data[threadid][i]
        else:
            return [][i]


class NonThreadedList(object):
    """Non-threaded list.

    NonThreadedList behaves like a normal list.  Its only purpose is
    to provide a compatible interface to PerThreadList, so that they
    can be used interchangeably.
    """

    def __init__(self):
        self.data = []

    def append(self, item):
        self.data.append(item)

    def extend(self, items):
        self.data.extend(items)

    def items(self, allThreads=False):
        return self.data

    def clear(self, allThreads=False):
        """Erases the list.

        We need this method, because it obviously won't work for user code
        to do: list = [].
        """
        self.data = []

    def __len__(self):
        return len(self.data)

    def __getitem__(self, i):
        return self.data[i]

    def isEmpty(self):
        """Test if the list is empty for all threads."""
        return len(self.data) == 0


if __name__ == '__main__':
    # just a few tests used in development
    def addItems():
        global s
        s.append(1)
        s.append(2)
    global i
    s = PerThreadList()
    for i in s:
        print i
    s.append(1)
    assert len(s) == 1
    s.append(2)
    s.append(3)
    assert len(s) == 3
    for i in s:
        print i
    from threading import Thread
    t = Thread(target=addItems)
    t.start()
    t.join()
    assert len(s) == 3
    assert len(s.items()) == 3
    assert len(s.items(allThreads=True)) == 5
    s.clear()
    assert len(s.items(allThreads=True)) == 2
    s.clear(allThreads=1)
    assert len(s.items(allThreads=True)) == 0
