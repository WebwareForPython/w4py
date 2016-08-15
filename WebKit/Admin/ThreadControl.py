from time import time, localtime, sleep

from WebUtils.Funcs import requestURI
from AdminSecurity import AdminSecurity

def strtime(t):
    return '%4d-%02d-%02d %02d:%02d:%02d' % localtime(t)[:6]


class ThreadControl(AdminSecurity):

    def title(self):
        return 'ThreadControl'

    def writeContent(self):
        app = self.application()
        server = app.server()
        request = self.request()
        field = request.field
        myRequestID = request.requestID()
        wr = self.writeln

        threadHandler = server._threadHandler
        abortRequest = server.abortRequest
        maxRequestTime = server.setting('MaxRequestTime', 0) or 0

        try:
            max_duration = int(field('duration'))
        except (KeyError, ValueError):
            max_duration = int(maxRequestTime/2) or 60

        wr('<h2>Current thread status</h2>',
            '<p>Automatic cancelation of long-running requests is controlled by'
            ' the <code>AppServer.config</code> setting <code>MaxRequestTime</code>.</p>')

        if maxRequestTime:
            wr('<p>Currently, this is set to <b>%d</b> seconds.</p>'
                % maxRequestTime)
        else:
            wr('<p>Currently, this setting is disabled.</p>')

        wr('<form action="ThreadControl" method="post">', '<p>')
        wr('<input name="cancel_all" type="submit"'
            ' value="Cancel all requests below">')
        wr('<input name="cancel_selected" type="submit"'
            ' value="Cancel all selected requests">')
        wr('<input name="refresh_view" type="submit"'
            ' value="Refresh view">', '</p>')
        wr('<p><input name="cancel_long" type="submit"'
            ' value="Cancel all long-running requests">'
            ' (longer than <input type="text" name="duration" value="%d"'
            ' size="6" maxlength="12" style="text-align: right">'
            ' seconds)</p>' % max_duration)
        wr('<p>You can <a href="Sleep" target="_blank">create a long-running'
            ' request</a> in a separate browser window for testing.</p>'
            '<p>(Your web browser may get stuck if it is waiting for more'
            ' than one of these.)</p>')

        if field('cancel_selected', None):
            killIDs = field('selectedIDs', None) or []
        elif field('cancel_all', None):
            killIDs = field('allIDs', '').split(',')
        elif field('cancel_long', None):
            killIDs = field('longIDs', None) or []
        else:
            killIDs = []
        if not isinstance(killIDs, list):
            killIDs = [killIDs]
        try:
            killIDs = map(int, killIDs)
        except ValueError:
            killIDs = []
        killedIDs = []
        errorIDs = []
        activeIDs = []
        for h in threadHandler.values():
            try:
                activeIDs.append(h._requestID)
            except AttributeError:
                continue
        for requestID in killIDs:
            if (not requestID or requestID == myRequestID
                    or requestID not in activeIDs):
                continue
            try:
                killed = abortRequest(requestID) == 1
            except Exception:
                killed = 0
            if killed:
                killedIDs.append(requestID)
            else:
                errorIDs.append(requestID)
        if killedIDs:
            msg = (len(killedIDs) > 1 and
                'The following requests have been canceled: %s'
                    % ', '.join(map(str, killedIDs)) or
                'Request %d has been canceled.' % killedIDs[0])
            wr('<p style="color:green">%s</p>' % msg)
            tries = 100
            while tries:
                pendingIDs = []
                for h in threadHandler.values():
                    try:
                        requestID = h._requestID
                        if requestID in killedIDs:
                            pendingIDs.append(requestID)
                    except AttributeError:
                        continue
                if pendingIDs:
                    sleep(0.125)
                    tries -= 1
                else:
                    pendingIDs = []
                    tries = 0
            if pendingIDs:
                msg = (len(pendingIDs) > 1 and
                    'The following of these are still pending: %s'
                        % ', '.join(map(str, pendingIDs)) or
                    'The request is still pending.')
                wr('<p>%s</p><p>You can'
                    ' <a href="ThreadControl">refresh the view<a>'
                    ' to verify cancelation.</p>' % msg)
        if errorIDs:
            msg = (len(errorIDs) > 1 and
                'The following requests could not be canceled: %s'
                    % ', '.join(map(str, errorIDs)) or
                'Request %d could not be canceled.' % errorIDs[0])
            wr('<p style="color:red">%s</p>' % msg)

        curTime = time()
        activeThreads = []
        try:
            threadCount = server._threadCount
        except AttributeError:
            threadCount = 0
        for t, h in threadHandler.items():
            try:
                name = t.getName()
                requestID = h._requestID
                requestDict = h._requestDict
                if requestID != requestDict['requestID']:
                    raise AttributeError
                startTime = requestDict.get('time')
                env = requestDict.get('environ')
                client = (env.get('REMOTE_NAME')
                    or env.get('REMOTE_ADDR')) if env else None
                uri = requestURI(env) if env else None
                activeThreads.append((name, requestID,
                    startTime, curTime - startTime, client, uri))
            except AttributeError:
                continue

        if activeThreads:
            headings = ('Thread name', 'Request ID', 'Start time',
                'Duration', 'Client', 'Request URI')
            sort = field('sort', None)
            wr('<table class="NiceTable"><tr>')
            column = 0
            sort_column = 1
            sort = field('sort', None)
            for heading in headings:
                sort_key = heading.lower().replace(' ', '_')
                if sort_key == sort:
                    sort_column = column
                wr('<th><a href="ThreadControl?sort=%s">%s</a></th>'
                    % (sort_key, heading))
                column += 1
            wr('<th>Cancel</th>')
            wr('</tr>')
            if sort_column:
                def key(t):
                    return t[sort_column], t[1]
            else:
                def key(t):
                    try:
                        n = int(t[0].rsplit('-', 1)[-1])
                    except ValueError:
                        n = 0
                    return n, t[0]
            activeThreads.sort(key=key)
        else:
            wr('<p>Could not determine the active threads.</p>')
        longIDs = []
        for (name, requestID, startTime, duration,
                client, uri) in activeThreads:
            if startTime:
                startTime = strtime(startTime)
                duration = int(duration + 0.5)
                if duration > 0:
                    if duration > max_duration:
                        duration = '<b>%s</b>' % duration
                        if requestID:
                            longIDs.append(requestID)
                    duration = '%s&nbsp;s' % duration
                else:
                    duration = int(1000*(duration) + 0.5)
                    duration = '%s&nbsp;ms' % duration
            else:
                duration = startTime = '-'
            if requestID and requestID != myRequestID:
                checkbox = ('<input type="hidden" name="allIDs" value="%d">'
                    '<input type="checkbox" name="selectedIDs" value="%d">'
                    % (requestID, requestID))
            else:
                checkbox = '&nbsp;'
            if not requestID:
                requestID = '-'
            elif requestID == myRequestID:
                requestID = '<b>%s</b>' % requestID
            if not client:
                client = '-'
            if uri:
                uri = uri.replace('/', '/' + '<wbr>')
            else:
                uri = '-'
            wr('<tr><td style="text-align:right">', name,
                '</td><td style="text-align:right">', requestID,
                '</td><td>', startTime,
                '</td><td style="text-align:right">', duration,
                '</td><td>', client, '</td><td>', uri, '</td>')
            wr('<td style="text-align:center">', checkbox, '</td>')
            wr('</tr>')
        if activeThreads:
            wr('</table>')
        longIDs = ','.join(map(str, longIDs))
        wr('<input type="hidden" name="longIDs" value="%s">' % longIDs)
        wr('</form>')

        if threadCount > len(activeThreads):
            wr('<p>Idle threads waiting for requests: <b>%d</b></p>' %
                (threadCount - len(activeThreads)))
        wr('<p>Current time: %s</p>' % strtime(curTime))
