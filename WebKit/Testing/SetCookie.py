import datetime
import time

from WebKit.SidebarPage import SidebarPage


cookieValues = [
    ('onclose', 'ONCLOSE'),
    ('expireNow', 'NOW'),
    ('expireNever', 'NEVER'),
    ('oneMinute', '+1m'),
    ('oneWeek', '+1w'),
    ('oneHourAndHalf', '+ 1h 30m'),
    ('timeIntTenSec', time.time() + 10),
    ('tupleOneYear', (time.localtime()[0] + 1,) + time.localtime()[1:]),
    ('dt1day', datetime.datetime.now() + datetime.timedelta(1)),
    ('dt2min', datetime.timedelta(minutes=2))
]


cookieIndex = 1


class SetCookie(SidebarPage):

    def cornerTitle(self):
        return 'Testing'

    def writeContent(self):
        global cookieIndex
        res = self.response()
        req = self.request()
        self.writeln('<h4>The time right now is:</h4>')
        self.writeln('<p>%s</p>'
            % time.strftime('%a, %d-%b-%Y %H:%M:%S GMT', time.gmtime()))
        self.writeln('<h2>Cookies received:</h2>\n')
        self.writeln('<ul>')
        for name, value in req.cookies().items():
            self.writeln('<li>%s = %s</li>'
                % (repr(name), self.htmlEncode(value)))
        self.writeln('</ul>')
        for name, expire in cookieValues:
            res.setCookie(name, 'Value #%i' % cookieIndex, expires=expire)
            cookieIndex += 1
        self.writeln('<h2>Cookies being sent:</h2>\n')
        self.writeln('<dl>')
        for name, cookie in res.cookies().items():
            self.writeln('<dt>%s sends:</dt>' % repr(name))
            self.writeln('<dd>%s</dd>'
                % self.htmlEncode(cookie.headerValue()))
        self.writeln('</dl>')
