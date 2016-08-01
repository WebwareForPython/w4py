import datetime

from Foo import Foo


def test(store):
    f = store.fetchObjectsOfClass(Foo)[0]

    value = f.d()
    match = None
    match = value == datetime.date(2000, 1, 1)
    assert match, value

    value = f.t()
    match = None
    match = value == store.filterDateTimeDelta(datetime.time(13, 01))
    if not match:
        match = value == datetime.timedelta(hours=13, minutes=01)
    assert match, '%s, %s' % (value, type(value))

    value = f.dt()
    match = None
    match = value == datetime.datetime(2000, 1, 1, 13, 1)
    assert match, value
