import datetime

import pyodbc

from SQLObjectStore import SQLObjectStore



class MSSQLObjectStore(SQLObjectStore):
    """MSSQLObjectStore implements an object store backed by a MSSQL database.

    pyodbc is required which you can get from here:
    http://code.google.com/p/pyodbc/

    Example creation:
        from MiddleKit.Run.MSSQLObjectStore import MSSQLObjectStore
        store = MSSQLObjectStore(driver='{SQL Server}', server='localhost',
            database='test', uid='me', pwd='me2')

    ODBC driver connection keywords are documented here:
    http://msdn.microsoft.com/de-de/library/ms131421.aspx

    See alsO: http://www.connectionstrings.com

    MSSQL defaults to autocommit on. If you want it off, set autocommit=False.
    """

    def __init__(self, **kwargs):
        self._autocommit = kwargs.get('autocommit', True)
        SQLObjectStore.__init__(self, **kwargs)

    def augmentDatabaseArgs(self, args, pool=False):
        if 'database' not in [arg.lower() for arg in args]:
            arg = args.get('ConnectionString')
            if not arg or 'database=' not in arg.lower():
                args['database'] = self._model.sqlDatabaseName()

    def newConnection(self):
        """Return a DB API 2.0 connection."""
        args = self._dbArgs.copy()
        self.augmentDatabaseArgs(args)
        arg = args.get('ConnectionString')
        arg = [arg] if arg else []
        return self.dbapiModule().connect(*arg, **args)

    def setting(self, name, default=NoDefault):
        if name == 'SQLConnectionPoolSize':
            return 0  # pyodbc comes already with pooling
        return SQLObjectStore.setting(self, name, default)

    def dbapiModule(self):
        return pyodbc

    def retrieveLastInsertId(self, conn, cur):
        newConn, cur = self.executeSQL('select @@IDENTITY', conn)
        try:
            value = int(cur.fetchone()[0])
        finally:
            if newConn and not conn:
                self.doneWithConnection(newConn)
        return value

    def filterDateTimeDelta(self, dtd):
        if isinstance(dtd, datetime.timedelta):
            dtd = datetime.datetime(1970, 1, 1) + dtd
        return dtd

    def sqlNowCall(self):
        return 'GETDATE()'


class Klass(object):

    def sqlTableName(self):
        """Return "[name]" so that table names do not conflict with SQL reserved words."""
        return '[%s]' % self.name()


class Attr(object):

    def sqlColumnName(self):
        if not self._sqlColumnName:
            self._sqlColumnName = '[' + self.name() + ']'
        return self._sqlColumnName


class ObjRefAttr(object):

    def sqlColumnName(self):
        if not self._sqlColumnName:
            if self.setting('UseBigIntObjRefColumns', False):
                # old way: one 64 bit column
                self._sqlColumnName = '[' + self.name() + 'Id' + ']'
            else:
                # new way: 2 int columns for class id and obj id
                self._sqlColumnName = '[%s],[%s]' % self.sqlColumnNames()
        return self._sqlColumnName


class StringAttr(object):

    def sqlForNonNone(self, value):
        return "'%s'" % value.replace("'", "''")  # do the right thing
