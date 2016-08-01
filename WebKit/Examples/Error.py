from ExamplePage import ExamplePage


class CustomError:
    """Custom classic class not based on Exception (for testing)."""

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class Error(ExamplePage):

    def title(self):
        return 'Error raising Example'

    def writeContent(self):
        error = self.request().field('error', None)
        if error:
            msg = 'You clicked that button!'
            if error.startswith('String'):
                error = msg
            elif error.startswith('Custom'):
                error = CustomError(msg)
            elif error.startswith('System'):
                error = SystemError(msg)
            else:
                error = StandardError(msg)
            self.writeln('<p>About to raise an error...</p>')
            raise error
        self.writeln('''<h1>Error Test</h1>
<form action="Error" method="post">
<p><select name="error" size="1">
<option selected>Standard Error</option>
<option>System Error</option>
<option>Custom Class (old)</option>
<option>String (deprecated)</option>
</select>
<input type="submit" value="Don't click this button!"></p>
</form>''')
