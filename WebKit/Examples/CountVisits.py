from ExamplePage import ExamplePage


class CountVisits(ExamplePage):
    """Counting visits example."""

    def writeContent(self):
        if self.request().hasField('expire'):
            self.session().expiring()
            self.sendRedirectAndEnd('CountVisits')
        self.writeln('<h3>Counting Visits</h3>')
        if self.request().isSessionExpired():
            self.writeln('<p><em>Your session has expired.</em></p>')
        count = self.session().value('count', 0) + 1
        self.session().setValue('count', count)
        self.writeln("""<p>You've been here
<strong style="background-color:yellow">&nbsp;%d&nbsp;</strong> time%s.</p>
<p>This page records your visits using a session object.
Every time you <a href="javascript:location.reload()">reload</a>
or <a href="CountVisits">revisit</a> this page, the counter will increase.
If you close your browser or force the session to
<a href="CountVisits?expire=1">expire</a>, then your session will end
and you will see the counter go back to 1 on your next visit.</p>
<p>Try hitting <a href="javascript:location.reload()">reload</a> now.</p>"""
            % (count, 's' if count > 1 else ''))
