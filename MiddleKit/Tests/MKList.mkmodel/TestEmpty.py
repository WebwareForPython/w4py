from Foo import Foo
from Bar import Bar


def NoException(codeString):
    raise Exception('Failed to raise exception for: ' + codeString)


def reset(store):
    store.clear()
    store.executeSQLTransaction(['delete from Foo;', 'delete from Bar;'])


def testAddToBars(store):
    # Test 1: Use addToBars()
    f = Foo()
    store.addObject(f)

    b = Bar()
    f.addToBars(b)
    b.dumpAttrs()
    store.saveChanges()

    store.clear()
    f = store.fetchObjectsOfClass(Foo)[0]
    bars = f.bars()
    assert len(bars) == 1, 'bars=%r' % bars
    assert bars[0].foo() == f
    reset(store)


def test(store):
    # We invoke testAddToBars twice on purpose, just to see that
    # the second time around, things are stable enough to pass again
    testAddToBars(store)
    testAddToBars(store)

    # Test 2: do not use addToBars()
    f = Foo()
    store.addObject(f)
    b = Bar()
    b.setFoo(f)
    b.setX(7)
    store.addObject(b)
    store.saveChanges()
    store.clear()

    f = store.fetchObjectsOfClass(Foo)[0]
    assert f._mk_store
    assert f._mk_inStore
    bars = f.bars()
    assert isinstance(bars, list)
    assert len(bars) == 1, 'bars=%r' % bars
    assert bars[0].x() == 7

    # Test addToXYZ() method
    bar = Bar()
    bar.setX(42)
    f.addToBars(bar)
    assert bar.foo() == f
    store.saveChanges()
    store.clear()

    f = store.fetchObjectsOfClass(Foo)[0]
    bars = f.bars()
    assert isinstance(bars, list)
    assert len(bars) == 2, 'bars=%r' % bars
    assert bars[0].x() == 7
    assert bars[1].x() == 42

    # Test the assertion checking in addToXYZ()
    try:
        f.addToBars(None)
    except Exception:
        pass
    else:
        NoException('f.addToBars(None)  # None not allowed')

    try:
        f.addToBars(5)
    except Exception:
        pass
    else:
        NoException('f.addToBars(5)  # not an object')

    try:
        f.addToBars(f)
    except Exception:
        pass
    else:
        NoException('f.addToBars(f)  # wrong class')

    try:
        f.addToBars(bar)
    except Exception:
        pass
    else:
        NoException('f.addToBars(bar)  # already added')

    # Test delFromXYZ() method
    bar = bars[1]
    f.delFromBars(bar)
    assert len(bars) == 1
    assert bar.foo() is None
    store.saveChanges()
    store.clear()

    f = store.fetchObjectsOfClass(Foo)[0]
    bars = f.bars()
    assert isinstance(bars, list)
    assert len(bars) == 1, 'bars=%r' % bars
    assert bars[0].x() == 7

    # Test the assertion checking in delFromXYZ()
    try:
        f.delFromBars(None)
    except Exception:
        pass
    else:
        NoException('f.delFromBars(None)  # None not allowed')

    try:
        f.delFromBars(5)
    except Exception:
        pass
    else:
        NoException('f.delFromBars(5)  # not an object')

    try:
        f.delFromBars(f)
    except Exception:
        pass
    else:
        NoException('f.delFromBars(f)  # wrong class')

    try:
        f.delFromBars(bar)
    except Exception:
        pass
    else:
        NoException('f.delFromBars(bar)  # already deleted')
