import os
from time import time, localtime, gmtime, asctime

from AdminSecurity import AdminSecurity


class Main(AdminSecurity):

    def title(self):
        return 'Admin'

    def writeContent(self):
        self.curTime = time()
        self.writeGeneralInfo()
        self.writeSignature()

    def writeGeneralInfo(self):
        app = self.application()
        info = (
            ('Webware Version', app.webwareVersionString()),
            ('WebKit Version',  app.webKitVersionString()),
            ('Local Time',      asctime(localtime(self.curTime))),
            ('Up Since',        asctime(localtime(app.server().startTime()))),
            ('Num Requests',    app.server().numRequests()),
            ('Working Dir',     os.getcwd()),
            ('Active Sessions', len(app.sessions()))
        )
        self.writeln('''
<h2 style="text-align:center">WebKit Administration Pages</h2>
<table style="margin-left:auto;margin-right:auto" class="NiceTable">
<tr class="TopHeading"><th colspan="2">Application Info</th></tr>''')
        for label, value in info:
            self.writeln('<tr><th style="text-align:left">%s:</th>'
                '<td>%s</td></tr>' % (label, value))
        self.writeln('</table>')

    def writeSignature(self):
        app = self.application()
        self.writeln('''
<!--
begin-parse
{
'Version': %r,
'LocalTime': %r,
'GlobalTime': %r
}
end-parse
-->''' % (app.webKitVersion(), localtime(self.curTime), gmtime(self.curTime)))
