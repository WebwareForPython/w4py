"""Mock python-memcached module."""

from copy import copy

data = dict()  # our mock memcache


class Client(object):
    """Mock memcache client."""

    def __init__(self, servers, debug=0, pickleProtocol=0):
        self._connected = True

    def set(self, key, val, time=0):
        if self._connected:
            if val is not None:
                data[key] = val
            return 1
        else:
            return 0

    def get(self, key):
        if self._connected:
            return copy(data.get(key))

    def delete(self, key, time=0):
        if self._connected:
            if key in data:
                del data[key]
            return 1
        else:
            return 0

    def disconnect_all(self):
        self._connected = False
