import difflib


def test(store):
    with open('Dump.csv', 'w') as samples:
        store.dumpObjectStore(samples)

    dumped = open('Dump.csv').readlines()
    expected = open('../MKDump.mkmodel/Samples.csv').readlines()
    diff = map(str.rstrip, difflib.context_diff(dumped, expected,
        fromfile='dumped.csv', tofile='expected.csv'))

    for line in diff:
        print line

    assert not diff
