from time import sleep

from WebKit.ThreadedAppServer import ThreadAbortedError
from AdminSecurity import AdminSecurity


class Sleep(AdminSecurity):

    def title(self):
        return 'Sleep'

    def writeContent(self):
        wr = self.writeln
        field = self.request().field
        try:
            duration = int(field("duration"))
        except (KeyError, ValueError):
            duration = 0
        maxRequestTime = self.application().server().setting(
            'MaxRequestTime', 0) or 0
        wr('''<form action="Sleep" method="post">
<input type="submit" name="action" value="Sleep">
<input type="text" name="duration" value="%d"
size="6" maxlength="12" style="text-align: right"> seconds
</form>''' % (duration or int(maxRequestTime*2) or 120))
        if duration:
            wr('<p>Sleeping %d seconds...</p>' % duration)
            self.response().flush(0)
            duration *= 8
            count = 0
            try:
                while count < duration:
                    # Don't block on system call or this thread can't be killed
                    sleep(0.125)
                    count += 1
                wr('<p>Time over, woke up!</p>')
            except ThreadAbortedError as e:
                duration = int((count+4)/8)
                wr('<p style="color:red">Sleep aborted with %s after %d seconds!</p>'
                    % (e.__class__.__name__, duration))
            wr('<p>Request %d has been processed.</p>'
                % self.request().requestID())
