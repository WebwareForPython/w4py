from Attr import Attr


class AnyDateTimeAttr(Attr):

    def __init__(self, attr):
        Attr.__init__(self, attr)


class DateTimeAttr(AnyDateTimeAttr):

    def __init__(self, attr):
        Attr.__init__(self, attr)


class DateAttr(AnyDateTimeAttr):

    def __init__(self, attr):
        Attr.__init__(self, attr)


class TimeAttr(AnyDateTimeAttr):

    def __init__(self, attr):
        Attr.__init__(self, attr)

# @@ 2000-10-13 ce: complete
