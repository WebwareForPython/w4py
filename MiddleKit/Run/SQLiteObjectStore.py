import sqlite3 as sqlite

from SQLObjectStore import SQLObjectStore


class SQLiteObjectStore(SQLObjectStore):
    """SQLiteObjectStore implements an object store backed by a SQLite database.

    See the SQLite docs or the DB API 2.0 docs for more information:
      https://docs.python.org/2/library/sqlite3.html
      https://www.python.org/dev/peps/pep-0249/
    """

    def augmentDatabaseArgs(self, args, pool=False):
        if not args.get('database'):
            args['database'] = '%s.db' % self._model.sqlDatabaseName()

    def newConnection(self):
        kwargs = self._dbArgs.copy()
        self.augmentDatabaseArgs(kwargs)
        return self.dbapiModule().connect(**kwargs)

    def dbapiModule(self):
        return sqlite

    def dbVersion(self):
        return "SQLite %s" % sqlite.sqlite_version

    def _executeSQL(self, cur, sql):
        try:
            cur.execute(sql)
        except sqlite.Warning:
            if not self.setting('IgnoreSQLWarnings', False):
                raise
        except sqlite.OperationalError as e:
            if 'database is locked' in str(e):
                print ('Please consider installing a newer SQLite version'
                    ' or increasing the timeout.')
            raise

    def sqlNowCall(self):
        return "datetime('now')"


class StringAttr(object):

    def sqlForNonNone(self, value):
        return "'%s'" % value.replace("'", "''")
