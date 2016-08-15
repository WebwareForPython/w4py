from MiscUtils.Funcs import uniqueId
from ExamplePage import ExamplePage


class LoginPage(ExamplePage):
    """A log-in screen for the example pages."""

    def title(self):
        return 'Log In'

    def htBodyArgs(self):
        return (ExamplePage.htBodyArgs(self)
            + ' onload="document.loginform.username.focus();"' % locals())

    def writeContent(self):
        self.writeln('<div style="margin-left:auto;margin-right:auto;width:20em">'
            '<p>&nbsp;</p>')
        request = self.request()
        extra = request.field('extra', None)
        if not extra and request.isSessionExpired() and not request.hasField('logout'):
            extra = 'You have been automatically logged out due to inactivity.'
        if extra:
            self.writeln('<p style="color:#333399">%s</p>' % self.htmlEncode(extra))
        if self.session().hasValue('loginid'):
            loginid = self.session().value('loginid')
        else:
            # Create a "unique" login id and put it in the form as well as in the session.
            # Login will only be allowed if they match.
            loginid = uniqueId(self)
            self.session().setValue('loginid', loginid)
        action = request.field('action', '')
        if action:
            action = ' action="%s"' % action
        self.writeln('''<p>Please log in to view the example.
The username and password is <kbd>alice</kbd> or <kbd>bob</kbd>.</p>
<form method="post" name="loginform"%s>
<table style="background-color:#CCCCEE;border:1px solid #3333CC;width:20em">
<tr><td style="text-align:right"><label for="username">Username:</label></td>
<td><input type="text" id="username" name="username" value="admin"></td></tr>
<tr><td style="text-align:right"><label for="password">Password:</label></td>
<td><input type="password" id="password" name="password" value=""></td></tr>
<tr><td colspan="2" style="text-align:right"><input type="submit" name="login" value="Login"></td></tr>
</table>
<input type="hidden" name="loginid" value="%s">''' % (action, loginid))
        # Forward any passed in values to the user's intended page after successful login,
        # except for the special values used by the login mechanism itself
        for name, value in request.fields().items():
            if name not in ('login', 'loginid', 'username', 'password', 'extra', 'logout'):
                if not isinstance(value, list):
                    value = [value]
                for v in value:
                    self.writeln('''<input type="hidden" name="%s" value="%s">'''
                        % (self.htmlEncode(name), self.htmlEncode(v)))
        self.writeln('</form>\n<p>&nbsp;</p></div>')
