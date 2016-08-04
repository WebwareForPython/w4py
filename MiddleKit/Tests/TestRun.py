#!/usr/bin/env python

"""Run MiddleKit test script."""

from TestCommon import *
import MiddleKit.Run


def test(filename, configFilename, pyFilename, deleteData):
    curDir = os.getcwd()
    os.chdir(workDir)
    try:
        filename = '../' + filename

        if os.path.splitext(filename)[1] == '':
            filename += '.mkmodel'
        pyFilename = os.path.join(filename, pyFilename)
        if not os.path.exists(pyFilename):
            print 'No such file', pyFilename
            return

        print 'Testing %s...' % filename

        # Set up the store
        names = {}
        src = 'from MiddleKit.Run.%sObjectStore import %sObjectStore as c' % (dbName, dbName)
        exec src in names
        objectStoreClass = names['c']
        store = objectStoreClass(**storeArgs)
        store.readModelFileNamed(filename, configFilename=configFilename)
        assert store.model()._havePythonClasses  # @@

        # Clear the database
        if deleteData:
            print 'Deleting all database records for test...'
            transaction = []
            for klass in store.model().klasses().values():
                if not klass.isAbstract():
                    transaction.append('delete from %s;' % klass.name())
            ObjectStore.Store.executeSQLTransaction(transaction)

        # Run the test
        results = {}
        execfile(pyFilename, results)
        assert 'test' in results, 'No test defined in %s.' % filename
        results['test'](store)
    finally:
        os.chdir(curDir)

def usage():
    print 'TestRun.py <model> <config file> <py file> [delete=no|yes]'
    print
    sys.exit(1)

def main():
    if len(sys.argv) < 4:
        usage()

    modelFilename = sys.argv[1]
    configFilename = sys.argv[2]
    pyFilename = sys.argv[3]
    deleteData = True
    if len(sys.argv) > 4:
        delArg = sys.argv[4]
        parts = delArg.split('=')
        if len(parts) != 2 or parts[0] != 'delete':
            usage()
        deleteData = parts[1].lower() in ('yes', 'true', '1')

    test(modelFilename, configFilename, pyFilename, deleteData)


if __name__ == '__main__':
    try:
        main()
    except:
        import traceback
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)
        # print '>> ABOUT TO EXIT WITH CODE 1'
        sys.exit(1)
