import new

import MySQLdb
from MySQLdb import Warning

from SQLObjectStore import SQLObjectStore


class MySQLObjectStore(SQLObjectStore):
    """MySQLObjectStore implements an object store backed by a MySQL database.

    MySQL notes:
      * MySQL home page: http://www.mysql.com.
      * MySQL version this was developed and tested with: 3.22.34 & 3.23.27
      * The platforms developed and tested with include Linux (Mandrake 7.1)
        and Windows ME.
      * The MySQL-Python DB API 2.0 module used under the hood is MySQLdb
        by Andy Dustman: http://dustman.net/andy/python/MySQLdb/.
      * Newer versions of MySQLdb have autocommit switched off by default.

    The connection arguments passed to __init__ are:
      - host
      - user
      - passwd
      - port
      - unix_socket
      - client_flag
      - autocommit

    You wouldn't use the 'db' argument, since that is determined by the model.

    See the MySQLdb docs or the DB API 2.0 docs for more information.
      http://www.python.org/topics/database/DatabaseAPI-2.0.html
    """

    def __init__(self, **kwargs):
        self._autocommit = kwargs.pop('autocommit', False)
        SQLObjectStore.__init__(self, **kwargs)

    def augmentDatabaseArgs(self, args, pool=False):
        if not args.get('db'):
            args['db'] = self._model.sqlDatabaseName()

    def newConnection(self):
        kwargs = self._dbArgs.copy()
        self.augmentDatabaseArgs(kwargs)
        conn = self.dbapiModule().connect(**kwargs)
        if self._autocommit:
            # MySQLdb 1.2.0 and later disables autocommit by default
            try:
                conn.autocommit(True)
            except AttributeError:
                pass
        return conn

    def connect(self):
        SQLObjectStore.connect(self)
        if self._autocommit:
            # Since our autocommit patch above does not get applied to pooled
            # connections, we have to monkey-patch the pool connection method
            try:
                pool = self._pool
                connection = pool.connection
            except AttributeError:
                pass
            else:
                def newConnection(self):
                    conn = self._normalConnection()
                    try:
                        conn.autocommit(True)
                    except AttributeError:
                        pass
                    return conn
                pool._normalConnection = connection
                pool._autocommit = self._autocommit
                pool.connection = new.instancemethod(
                    newConnection, pool, pool.__class__)

    def retrieveLastInsertId(self, conn, cur):
        try:
            # MySQLdb module 1.2.0 and later
            lastId = conn.insert_id()
        except AttributeError:
            # MySQLdb module 1.0.0 and earlier
            lastId = cur.insert_id()
        # The above is more efficient than this:
        # conn, cur = self.executeSQL('select last_insert_id();', conn)
        # id = cur.fetchone()[0]
        return lastId

    def dbapiModule(self):
        return MySQLdb

    def _executeSQL(self, cur, sql):
        try:
            cur.execute(sql)
        except MySQLdb.Warning:
            if not self.setting('IgnoreSQLWarnings', False):
                raise

    def sqlNowCall(self):
        return 'NOW()'


# Mixins

class StringAttr(object):

    def sqlForNonNone(self, value):
        """MySQL provides a quoting function for string -- this method uses it."""
        return "'" + MySQLdb.escape_string(value) + "'"
