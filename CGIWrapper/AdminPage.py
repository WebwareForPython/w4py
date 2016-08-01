

class AdminPage(object):
    """AdminPage

    This is the abstract superclass of all CGI Wrapper administration CGI
    classes. Subclasses typically override title() and writeBody(), but may
    customize other methods. Subclasses use self._var for the various vars
    that are passed in from CGI Wrapper and self.write() and self.writeln().

    """


    ## Init ##

    def __init__(self, vars):
        for name in vars:
            setattr(self, '_' + name, vars[name])
        self._vars = vars


    ## HTML ##

    def html(self):
        self._html = []
        self.writeHeader()
        self.writeBody()
        self.writeFooter()
        return ''.join(self._html)


    ## Utility methods ##

    def write(self, *args):
        for arg in args:
            self._html.append(str(arg))

    def writeln(self, *args):
        for arg in args:
            self._html.append(str(arg))
        self._html.append('\n')


    ## Content methods ##

    def writeHeader(self):
        self.writeln('''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
    <title>%s</title>
</head>
<body %s>
        <table align="center" bgcolor="white"><tr><td>''' % (
            self.title(), self.bodyTags()))
        self.writeBanner()
        self.writeToolbar()

    def writeBody(self):
        raise NotImplementedError('Should be overridden in a subclass')

    def writeFooter(self):
        self.writeln('''
        <hr>
        <div align="center" style="font-size:small">Webware for Python</div>
        </td></tr></table>
</body>
</html>''')

    def title(self):
        raise NotImplementedError('Should be overridden in a subclass')

    def bodyTags(self):
        return 'text="black" bgcolor="#555555"'

    def writeBanner(self):
        self.writeln('''
        <table align="center" bgcolor="#202080" cellpadding="5" cellspacing="0" width="100%%">
            <tr><td align="center" style="color:white;font-weight:bold;font-family:Tahoma,Verdana,Arial,Helvetica,sans-serif">
                <div style="font-size:14pt">CGI Wrapper</div>
                <div style="font-size:16pt">%s</div>
            </td></tr>
        </table>''' % self.title())

    def writeToolbar(self):
        pass
