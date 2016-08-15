from ExamplePage import ExamplePage


class RequestInformation(ExamplePage):
    """Request information demo."""

    def writeContent(self):
        self.writeln('<h3>Request Variables</h3>')
        self.writeln('<p>The following table'
            ' shows the values for various request variables.</p>')
        self.writeln('<table style="font-size:small;width:100%">')
        request = self.request()
        self.showDict('fields()', request.fields())
        self.showDict('environ()', request.environ())
        self.showDict('cookies()', request.cookies())
        self.writeln('</table>')
        setCookie = self.response().setCookie
        setCookie('TestCookieName', 'CookieValue')
        setCookie('TestExpire1', 'expires in 1 minute', expires='+1m')

    def showDict(self, name, d):
        self.writeln('<tr style="vertical-align:top">'
            '<td style="background-color:#CCF" colspan="2">%s</td>'
            '</tr>' % name)
        for key in sorted(d):
            self.writeln(
                '<tr style="vertical-align:top;background-color:#EEF">'
                '<td>%s</td><td>%s</td></tr>' % (key, self.htmlEncode(
                str(d[key])).replace('\n', '<br>').replace(
                ',', ',<wbr>').replace(';', ';<wbr>').replace(':/', ':<wbr>/')))
