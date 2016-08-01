#!/usr/bin/env python

"""Execute SQL script using the nonstandard DB API executescript() method."""

from TestCommon import *
import MiddleKit.Run


def run(filename):
    # Set up the store
    names = {}
    src = 'from MiddleKit.Run.%sObjectStore import %sObjectStore as c' % (dbName, dbName)
    exec src in names
    objectStoreClass = names['c']
    store = objectStoreClass(**storeArgs)

    if filename == '--version':
        # Print database version
        print "%s (%s)" % (store.dbVersion(), store.dbapiVersion())
    else:
        # Open the script file
        filename = os.path.normpath(filename)
        if not os.path.exists(filename):
            print 'No such file', filename
            return

        print 'Executing %s...' % filename

        # Read the script
        sql = open(filename).read()

        # Execute the script
        curDir = os.getcwd()
        os.chdir(workDir)
        try:
            store.executeSQLScript(sql)
        finally:
            os.chdir(curDir)

def usage():
    print 'ExecuteScript.py <sql file>'
    print
    sys.exit(1)

def main():
    if len(sys.argv) < 2:
        usage()
    filename = sys.argv[1]
    run(filename)


if __name__ == '__main__':
    try:
        main()
    except:
        import traceback
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)
        # print '>> ABOUT TO EXIT WITH CODE 1'
        sys.exit(1)
