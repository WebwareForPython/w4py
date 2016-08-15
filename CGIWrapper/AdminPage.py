

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
        self.writeln('''<!DOCTYPE html>
<html>
<head>
    <title>%s</title>
</head>
<body %s>
    <table style="margin-left:auto;margin-right:auto;background-color:white">
        <tr><td>''' % (
            self.title(), self.bodyArgs()))
        self.writeBanner()
        self.writeToolbar()

    def writeBody(self):
        raise NotImplementedError('Should be overridden in a subclass')

    def writeFooter(self):
        self.writeln('''
        <hr>
        <div style="text-align:center;font-size:small">Webware for Python</div>
        </td></tr>
    </table>
</body>
</html>''')

    def title(self):
        raise NotImplementedError('Should be overridden in a subclass')

    def bodyArgs(self):
        return 'style="color:#000000;background-color:#555555"'

    def writeBanner(self):
        self.writeln('''
        <table style="margin-left:auto;margin-right:auto;background-color:#202080;border-spacing:0;width:100%%">
            <tr><td style="text-align:center;padding:5px;color:white;font-weight:bold;font-family:Tahoma,Verdana,Arial,Helvetica,sans-serif">
                <div style="font-size:14pt">CGI Wrapper</div>
                <div style="font-size:16pt">%s</div>
            </td></tr>
        </table>''' % self.title())

    def writeToolbar(self):
        pass
