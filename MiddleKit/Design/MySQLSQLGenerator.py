from SQLGenerator import SQLGenerator


class MySQLSQLGenerator(SQLGenerator):

    def sqlSupportsDefaultValues(self):
        return True


class Klasses(object):

    def dropDatabaseSQL(self, dbName):
        return 'drop database if exists %s;\n' % dbName

    def dropTablesSQL(self):
        sql = []
        for tableName in reversed(self.auxiliaryTableNames()):
            sql.append('drop table if exists %s;\n' % tableName)
        for klass in reversed(self._model._allKlassesInOrder):
            sql.append('drop table if exists %s;\n' % klass.name())
        sql.append('\n')
        return ''.join(sql)

    def createDatabaseSQL(self, dbName):
        return 'create database %s;\n' % dbName

    def useDatabaseSQL(self, dbName):
        return 'use %s;\n\n' % dbName

    def listTablesSQL(self):
        return 'show tables\n\n'


class Klass(object):

    def writePostCreateTable(self, generator, out):
        start = self.setting('StartingSerialNum', None)
        if start:
            out.write('alter table %s auto_increment=%s;\n' % (
                self.sqlTableName(), start))

    def primaryKeySQLDef(self, generator):
        return '    %s int not null primary key auto_increment,\n' % (
            self.sqlSerialColumnName().ljust(self.maxNameWidth()),)

    def writeIndexSQLDefsInTable(self, wr):
        for attr in self.allAttrs():
            if attr.boolForKey('isIndexed') and attr.hasSQLColumn():
                wr(',\n')
                wr('    index (%s)' % attr.sqlName())
        wr('\n')


class EnumAttr(object):

    def nativeEnumSQLType(self):
        return 'enum(%s)' % ', '.join(['"%s"' % enum for enum in self.enums()])


class StringAttr(object):

    def sqlType(self):
        # @@ 2000-11-11 ce: cache this
        if not self.get('Max'):
            return 'varchar(100) /* WARNING: NO LENGTH SPECIFIED */'
        max = int(self['Max'])  # @@ 2000-11-12 ce: won't need int() after using types
        if max > 65535:
            return 'longtext'
        if max > 255:
            return 'text'
        if self.get('Min') and int(self['Min']) == max:
            return 'char(%s)' % max
        else:
            return 'varchar(%s)' % max


class ObjRefAttr(object):

    def sqlType(self):
        if self.setting('UseBigIntObjRefColumns', False):
            return 'bigint unsigned /* %s */' % self['Type']
        else:
            return 'int unsigned'
