import os

def test(store):
    with open('Dump.csv', 'w') as samples:
        store.dumpObjectStore(samples)

    command = 'diff -u ../MKDump.mkmodel/Samples.csv Dump.csv'
    print command
    retval = os.system(command)
    retval >>= 8  # upper byte is the return code

    assert retval == 0
