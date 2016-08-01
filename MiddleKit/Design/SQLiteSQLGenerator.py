import os

from SQLGenerator import SQLGenerator


class SQLiteSQLGenerator(SQLGenerator):

    def sqlSupportsDefaultValues(self):
        return True


class Model(object):

    def writeConnectToDatabase(self, generator, output, databasename):
        pass


class Klasses(object):

    def dropDatabaseSQL(self, dbName):
        return self.dropTablesSQL()

    def dropTablesSQL(self):
        sql = []
        for tableName in reversed(self.auxiliaryTableNames()):
            sql.append('drop table if exists %s;\n' % tableName)
        for klass in reversed(self._model._allKlassesInOrder):
            sql.append('drop table if exists %s;\n' % klass.name())
        sql.append('\n')
        return ''.join(sql)

    def createDatabaseSQL(self, dbName):
        return ''

    def useDatabaseSQL(self, dbName):
        return ''

    def listTablesSQL(self):
        return ''


class Klass(object):

    def primaryKeySQLDef(self, generator):
        return '    %s integer primary key autoincrement,\n' % (
            self.sqlSerialColumnName().ljust(self.maxNameWidth()),)

    def writeIndexSQLDefs(self, wr):
        # in SQLite, indices must be created with 'create index' commands
        pass


class EnumAttr(object):

    def writeAuxiliaryCreateTable(self, generator, out):
        if self.usesExternalSQLEnums():
            out.write('drop table if exists %s;\n' % self.externalEnumsSQLNames()[0])
        EnumAttr.mixInSuperWriteAuxiliaryCreateTable(self, generator, out)


class StringAttr(object):

    def sqlType(self):
        return 'text'

    def sqlForNonNoneSampleInput(self, value):
        return "'%s'" % value.replace("'", "''")


class ObjRefAttr(object):

    def sqlType(self):
        return 'integer /* %s */' % self['Type']

