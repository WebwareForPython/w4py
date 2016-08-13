
try:  # psycopg2 version 2
    from psycopg2 import Warning, DatabaseError
    from psycopg2.extensions import QuotedString
except ImportError:  # psycopg version 1
    try:
        from psycopg import Warning, DatabaseError
        from psycopg.extensions import QuotedString
    except ImportError:  # PyGreSQL
        from pgdb import Warning, DatabaseError
        def QuotedString(s):
            return "'%s'" % s.replace("\\", "\\\\").replace("'", "''")

from MiscUtils.MixIn import MixIn

from SQLGenerator import SQLGenerator
from SQLGenerator import PrimaryKey as PrimaryKeyBase


class PostgreSQLSQLGenerator(SQLGenerator):

    def sqlSupportsDefaultValues(self):
        return True


class Model(object):

    def writeConnectToDatabase(self, generator, output, databasename):
        output.write('\c %s;\n\n' % databasename)

    def writePostSamplesSQL(self, generator, output):
        # after inserting the samples, update the sequences with the highest
        # serial numbers we've seen for each class.
        for klass in self._allKlassesInOrder:
            if hasattr(klass, '_maxSerialNum') and klass._maxSerialNum > 0:
                output.write("select setval('%s', %d);"
                    % (klass.seqName(), klass._maxSerialNum))


class Klasses(object):

    def writeClassIdsSQL(self, generator, out):
        # pgsql 7.3.4 doesn't seem to drop the _MKClassIDs table when the database
        # is dropped.  very strange.  Anyways, we drop it here just to make sure.
        out.write('\ndrop table _MKClassIds cascade;\n')
        Klasses.mixInSuperWriteClassIdsSQL(self, generator, out)

    def dropDatabaseSQL(self, dbName):
        # errors are ignored
        return 'drop database "%s";\n' % dbName

    def dropTablesSQL(self):
        sql = []
        for tableName in reversed(self.auxiliaryTableNames()):
            sql.append('drop table "%s";\n' % tableName)
        for klass in reversed(self._model._allKlassesInOrder):
            sql.append('drop table "%s";\n' % klass.name())
        sql.append('\n')
        return ''.join(sql)

    def createDatabaseSQL(self, dbName):
        return 'create database "%s";\n' % dbName

    def useDatabaseSQL(self, dbName):
        return '\c "%s"\n\n' % dbName

    def listTablesSQL(self):
        return '\d\n\n'


class Klass(object):

    def writeCreateSQL(self, generator, out):
        # create the sequences explicitly, just to be sure
        wr = out.write
        if not self.isAbstract():
            wr('create sequence %s start 1 minvalue 1;\n\n' % self.seqName())
        Klass.mixInSuperWriteCreateSQL(self, generator, out)
        self.writePgSQLIndexDefs(wr)

    def seqName(self):
        return '%s_%s_seq' % (self.sqlTableName(), self.sqlSerialColumnName())

    def writeIndexSQLDefs(self, wr):
        # in PostgreSQL, indices must be created with 'create index' commands
        pass

    def writePgSQLIndexDefs(self, wr):
        for attr in self.allAttrs():
            if attr.get('isIndexed', 0) and attr.hasSQLColumn():
                wr('create index %s_%s_index on %s (%s);\n'
                    % (self.sqlTableName(), attr.sqlName(),
                    self.sqlTableName(), attr.sqlName()))
        wr('\n')

    def primaryKeySQLDef(self, generator):
        return "    %s integer not null primary key default nextval('%s'),\n" % (
            self.sqlSerialColumnName(), self.seqName())


class StringAttr(object):

    def sqlType(self):
        # @@ 2000-11-11 ce: cache this
        if not self.get('Max'):
            return 'varchar(100) /* WARNING: NO LENGTH SPECIFIED */'
        max = int(self['Max'])  # @@ 2000-11-12 ce: won't need int() after using types
        if max > 255:
            return 'text'
        if self.get('Min') and int(self['Min']) == max:
            return 'char(%s)' % max
        else:
            return 'varchar(%s)' % max

    def sqlForNonNoneSampleInput(self, value):
        return "%s" % QuotedString(value)


class BoolAttr(object):

    def sqlForNonNoneSampleInput(self, value):
        value = value.upper()
        if value in ('FALSE', 'NO'):
            value = 'TRUE'
        elif value in ('TRUE', 'YES'):
            value = 'FALSE'
        else:
            try:
                value = int(value)
                if value == 0:
                    value = 'FALSE'
                elif value == 1:
                    value = 'TRUE'
            except Exception:
                pass
        assert value in ('TRUE', 'FALSE'), (
            "'%s' is not a valid default for boolean column '%s'"
            % (value, self.name()))
        return value


class DateTimeAttr(object):

    def sqlType(self):
        # In accord with newer PostgreSQL versions,
        # we use timestamps *without* time zone by default.
        # This also makes DateTime more compatible with the MySQL variant.
        # It is recommended to simply store all DateTimes as UTC.
        return 'timestamp'


class ObjRefAttr(object):

    def sqlType(self):
        return 'bigint /* %s */' % self['Type']


class PrimaryKey(object):

    def sampleValue(self, value):
        # keep track of the highest serial number for each klass,
        # so that we can update the database sequences
        if int(value) > self._klass._maxSerialNum:
            self._klass._maxSerialNum = int(value)
        return value

# PrimaryKey is not a core class, so we have to mix this in manually.
MixIn(PrimaryKeyBase, PrimaryKey)
