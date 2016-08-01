class NoException(Exception):
    pass


def test(store):
    from Foo import Foo

    f = Foo()

    # Test defaults
    assert f.b() == 1
    assert f.i() == 2
    assert f.l() == 3
    assert f.f() == 4
    assert f.s() == '5'
    assert f.e() == 'x'

    # Test min max
    # These should pass
    for x in range(10):
        f.setI(int(x))
        f.setL(long(x))
        f.setF(float(x))
    for x in range(6):
        s = '.'*(x+5)
        f.setS(s)

    # Test min max
    # These should throw exceptions
    if 0:
        for x in [-1, 11]:
            try:
                f.setI(int(x))
            except Exception:
                pass
            else:
                raise NoException

    # We'd like to test that the SQL code has the correct
    # DEFAULTs. Testing the sample values can't do this
    # because the SQL generated for inserting samples
    # uses the defaults specified in the object model.
    # So we use some direct SQL here:
    if getattr(store, 'executeSQL'):
        store.executeSQLTransaction('insert into Foo (i) values (42);')
        foo = store.fetchObjectsOfClass(Foo, clauses='where i=42')[0]
        assert foo.valueForKey('b') == 1, foo.valueForKey('b')
        assert foo.valueForKey('l') == 3, foo.valueForKey('l')
        assert foo.valueForKey('f') == 4, foo.valueForKey('f')
        assert foo.valueForKey('s') == '5', foo.valueForKey('s')

        store.executeSQLTransaction('insert into Foo (s) values (42);')
        foo = store.fetchObjectsOfClass(Foo, clauses="where s='42'")[0]
        assert foo.valueForKey('i') == 2
