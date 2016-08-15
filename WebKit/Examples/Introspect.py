from ExamplePage import ExamplePage


class Introspect(ExamplePage):

    def writeContent(self):
        self.writeln('<h4>Introspection</h4>')
        self.writeln("<p>The following table shows the values for various"
            " Python expressions, all of which are related to <em>introspection</em>."
            " That is to say, all the expressions examine the environment such as"
            " the object, the object's class, the module and so on.</p>")
        self.writeln('<table style="width:100%;background-color:#EEEEFF">')
        self.pair('locals().keys()', locals().keys())
        self.list('globals().keys()')
        self.list('dir(self)')
        self.list('dir(self.__class__)')
        self.list('self.__class__.__bases__')
        self.list('dir(self.__class__.__bases__[0])')
        self.writeln('</table>')

    def pair(self, key, value):
        if isinstance(value, (list, tuple)):
            value = ', '.join(map(str, value))
        self.writeln('<tr style="vertical-align:top"><td>%s</td>'
            '<td>%s</td></tr>' % (key, self.htmlEncode(str(value))))

    def list(self, codeString):
        value = eval(codeString)
        assert isinstance(value, (list, tuple))
        self.pair(codeString, value)
