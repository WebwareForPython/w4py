
connectionPool = True
try:
    import psycopg2 as dbi  # psycopg2 version 2
    from psycopg2 import Warning, DatabaseError
    from psycopg2.extensions import QuotedString
except ImportError:
    try:
        import psycopg as dbi  # psycopg version 1
        from psycopg import Warning, DatabaseError
        from psycopg.extensions import QuotedString
    except ImportError:
        connectionPool = False
        import pgdb as dbi  # PyGreSQL
        from pgdb import Warning, DatabaseError
        def QuotedString(s):
            return "'%s'" % s.replace("\\", "\\\\").replace("'", "''")

from MiscUtils import NoDefault
from MiscUtils.MixIn import MixIn
from MiddleKit.Run.ObjectKey import ObjectKey
from MiddleObject import MiddleObject

from SQLObjectStore import SQLObjectStore, UnknownSerialNumberError


class PostgreSQLObjectStore(SQLObjectStore):
    """PostgresObjectStore implements an object store backed by a PostgreSQL database.

    The connection arguments passed to __init__ are:
      - host
      - user
      - passwd
      - port
      - unix_socket
      - client_flag

    You wouldn't use the 'db' argument, since that is determined by the model.
    """

    def augmentDatabaseArgs(self, args, pool=False):
        if not args.get('database'):
            args['database'] = self._model.sqlDatabaseName()

    def newConnection(self):
        args = self._dbArgs.copy()
        self.augmentDatabaseArgs(args)
        return self.dbapiModule().connect(**args)

    if connectionPool:

        # psycopg doesn't seem to work well with DBPool. Besides, it does
        # its own connection pooling internally, so DBPool is unnecessary.

        def setting(self, name, default=NoDefault):
            if name == 'SQLConnectionPoolSize':
                return 0
            return SQLObjectStore.setting(self, name, default)

        # psycopg doesn't like connections to be closed because of pooling

        def doneWithConnection(self, conn):
            pass

    def newCursorForConnection(self, conn, dictMode=False):
        return conn.cursor()

    def retrieveNextInsertId(self, klass):
        seqname = "%s_%s_seq" % (klass.name(), klass.sqlSerialColumnName())
        conn, curs = self.executeSQL("select nextval('%s')" % seqname)
        value = curs.fetchone()[0]
        assert value, "Didn't get next id value from sequence"
        return value

    def dbapiModule(self):
        return dbi

    def _executeSQL(self, cur, sql):
        try:
            cur.execute(sql)
        except Warning:
            if not self.setting('IgnoreSQLWarnings', False):
                raise

    def saveChanges(self):
        conn, cur = self.connectionAndCursor()
        try:
            SQLObjectStore.saveChanges(self)
        except DatabaseError:
            conn.rollback()
            raise
        except Warning:
            if not self.setting('IgnoreSQLWarnings', False):
                conn.rollback()
                raise
        conn.commit()

    def sqlCaseInsensitiveLike(self, a, b):
        return "%s ilike %s" % (a, b)

    def sqlNowCall(self):
        return 'now()'


class StringAttr(object):

    def sqlForNonNone(self, value):
        """psycopg provides a quoting function for string -- use it."""
        return "%s" % QuotedString(value)


class BoolAttr(object):

    def sqlForNonNone(self, value):
        if value:
            return 'TRUE'
        else:
            return 'FALSE'
