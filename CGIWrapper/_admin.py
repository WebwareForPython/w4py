"""CGIWrapper main admin script."""

from time import time, localtime, gmtime, asctime

from WebUtils.Funcs import urlEncode
from AdminPage import AdminPage


class Page(AdminPage):
    """CGIWrapper main administration page."""

    def title(self):
        return 'Admin'

    def writeBody(self):
        curTime = time()
        self.writeln('''
        <table style="margin-left:auto;margin-right:auto">
            <tr><th>Version:</th><td>%s</td></tr>
            <tr><th>Local time:</th><td>%s</td></tr>
            <tr><th>Global time:</th><td>%s</td></tr>
        </table>''' % (
            self._wrapper.version(),
            asctime(localtime(curTime)), asctime(gmtime(curTime))))
        self.startMenu()
        self.menuItem('Script log contents', '_dumpCSV?filename=%s' %
            urlEncode(self._wrapper.setting('ScriptLogFilename')))
        self.menuItem('Error log contents', '_dumpErrors?filename=%s' %
            urlEncode(self._wrapper.setting('ErrorLogFilename')))
        self.menuItem('Show config', '_showConfig')
        self.endMenu()

        self.writeln('''
<!--
begin-parse
{
'Version': %r,
'LocalTime': %r,
'GlobalTime': %r
}
end-parse
-->''' % (self._wrapper.version(), localtime(curTime), gmtime(curTime)))

    def startMenu(self):
        self.write('''
        <div style="font-size:12pt;font-family:Arial,Helvetica,sans-serif">
        <table style="margin-left:auto;margin-right:auto;background-color:#E8E8F0">
            <tr style="background-color:#101040"><th style="text-align:center;color:white">Menu</th></tr>''')

    def menuItem(self, title, url):
        self.write('''
            <tr><td style="text-align:center"><a href="%s">%s</a></td></tr>''' % (
                url, title))

    def endMenu(self):
        self.writeln('''
        </table>
        </div>''')
