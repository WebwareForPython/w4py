
from WebKit.SidebarPage import SidebarPage


class FieldStorage(SidebarPage):
    """Test the FieldStorage class.

    Since WebKit 0.6, WebKit uses a modified FieldStorage class that
    parses GET parameters even in a POST request. However, the parameter
    names must be different. A GET parameters with the same name as a
    POST parameter is ignored, these values are not appended. In other words,
    POST parameters always override GET parameters with the same name.
    """

    def cornerTitle(self):
        return 'Testing'

    def writeContent(self):
        request = self.request()
        method = request.method()
        fields = request.fields()
        writeln = self.writeln
        if method == 'GET' and not fields:
            get_fields = [('getfield1', 'getvalue1'),
                ('getfield2', 'getvalue21'), ('getfield2', 'getvalue22'),
                ('dualfield1', 'getdual1'),
                ('dualfield2', 'getdual21'), ('dualfield2', 'getdual22'),
                ('getempty', '')]
            post_fields = [('postfield1', 'postvalue1'),
                ('postfield2', 'postvalue21'), ('postfield2', 'postvalue22'),
                ('dualfield1', 'postdual1'),
                ('dualfield2', 'postdual21'), ('dualfield2', 'postdual22'),
                ('postempty', '')]
            writeln('<p>The WebKit FieldStorage class can be tested here.</p>')
            writeln('<form action="FieldStorage?%s" method="POST">'
                % '&amp;'.join('%s=%s' % field for field in get_fields))
            writeln('<p>Please press the button to run the test:')
            for field in post_fields:
                writeln('<input type="hidden" name="%s" value="%s">' % field)
            writeln('<input type="submit" name="testbutton" value="Submit">')
            writeln('</p></form>')
        else:
            errors = []
            error = errors.append
            if method != 'POST':
                error('The method is %s instead of POST' % method)
            if len(fields) != 9:
                error('We got %d instead of 9 fields' % len(fields))
            if not request.hasField('testbutton'):
                error('We did not get the submit button')
            elif request.field('testbutton') != 'Submit':
                error('The submit button field got a wrong value')
            if not request.hasField('getempty'):
                error('We did not get the empty GET parameter')
            elif request.field('getempty') != '':
                error('The empty GET field got a non-empty value')
            if not request.hasField('postempty'):
                error('We did not get the empty POST parameter')
            elif request.field('postempty') != '':
                error('The empty POST field got a non-empty value')
            if not request.hasField('getfield1'):
                error('The first GET parameter has not been passed')
            elif request.field('getfield1') != 'getvalue1':
                error('The first GET field got a wrong value')
            if not request.hasField('postfield1'):
                error('The first POST parameter has not been passed')
            elif request.field('postfield1') != 'postvalue1':
                error('The first POST field got a wrong value')
            if not request.hasField('getfield2'):
                error('The second GET parameter has not been passed')
            elif request.field('getfield2') != ['getvalue21', 'getvalue22']:
                error('The second GET field got a wrong value')
            if not request.hasField('postfield2'):
                error('The second POST parameter has not been passed')
            elif request.field('postfield2') != ['postvalue21', 'postvalue22']:
                error('The second POST field got a wrong value')
            if not request.hasField('dualfield1'):
                error('The first dual parameter has not been passed')
            elif request.field('dualfield1') == 'getdual1':
                error('The first dual field was not overridden via POST')
            elif request.field('dualfield1') in (
                    ['getdual1', 'postdual1'], ['postdual1', 'getdual1']):
                error('The first dual field'
                    ' was extended instead of overridden via POST')
            elif request.field('dualfield1') != 'postdual1':
                error('The first dual field got a wrong value')
            if not request.hasField('dualfield2'):
                error('The second dual parameter has not been passed')
            elif request.field('dualfield2') == ['getdual21', 'getdual22']:
                error('The second dual field was not overridden via POST')
            elif request.field('dualfield2') in (
                    ['getdual21', 'getdual22', 'postdual21', 'postdual22'],
                    ['postdual21', 'postdual22', 'getdual21', 'getdual22']):
                error('The second dual field'
                    ' was extended instead of overridden via POST')
            elif request.field('dualfield2') != ['postdual21', 'postdual22']:
                error('The second dual field got a wrong value')
            if errors:
                writeln('<p>FieldStorage does <b>not</b> work as expected:</p>')
                writeln('<ul>')
                for error in errors:
                    writeln('<li>%s.</li>' % error)
                writeln('</ul>')
            else:
                writeln('<p>Everything ok, FieldStorage works as expected.</p>')
            writeln('<p><a href="./">Back to the test cases overview.</a></p>')
