"""Mock redis-py module."""

from copy import copy

data = dict()  # our mock redis


class ConnectionPool(object):

    def __init__(self, redis):
        self._redis = redis

    def disconnect(self):
        self._redis._connected = False


class StrictRedis(object):
    """Mock Redis client."""

    def __init__(self, host='localhost', port=6379, db=0, password=None):
        self.connection_pool = ConnectionPool(self)
        self._connected = True

    def setex(self, name, time, value):
        if self._connected:
            if value is not None:
                data[name] = value

    def get(self, name):
        if self._connected:
            return copy(data.get(name))

    def delete(self, *names):
        if self._connected:
            for name in names:
                del data[name]

    def exists(self, name):
        if self._connected:
            return name in data

    def keys(self, pattern='*'):
        if self._connected:
            if not pattern.endswith('*'):
                raise ValueError('bad pattern')
            pattern = pattern[:-1]
            if not pattern:
                return data.keys()
            return [k for k in data if k.startswith(pattern)]

    def flushdb(self):
        if self._connected:
            data.clear()
