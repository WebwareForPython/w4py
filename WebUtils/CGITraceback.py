"""More comprehensive traceback formatting for Python scripts.

Original version know as cgitb written By Ka-Ping Yee <ping@lfw.org>
Modified for Webware by Ian Bicking <ianb@colorstudy.com>
"""

import inspect
import keyword
import linecache
import os
import pydoc
import sys
import tokenize
from types import MethodType


pyhtml = pydoc.html
escape = pyhtml.escape


DefaultOptions = {
    'table': 'background-color:#F0F0F0',
    'default': 'color:#000000',
    'row.location': 'color:#000099',
    'row.code': 'color:#990000',
    'header': 'color:#FFFFFF;background-color:#999999',
    'subheader': 'color:#000000;background-color:#F0F0F0;font-size:10pt',
    'code.accent': 'background-color:#FFFFCC',
    'code.unaccent': 'color:#999999;font-size:10pt',
}


def breaker():
    return ('<body style="background-color:#F0F0FF">' +
        '<span style="color:#F0F0FF;font-size:small"> > </font> ' +
        '</table>' * 5)


def html(context=5, options=None):
    if options:
        opt = DefaultOptions.copy()
        opt.update(options)
    else:
        opt = DefaultOptions

    etype, evalue = sys.exc_info()[:2]
    if not isinstance(etype, basestring):
        etype = etype.__name__
    inspect_trace = inspect.trace(context)

    pyver = 'Python ' + sys.version.split(None, 1)[0] + '<br>' + sys.executable
    javascript = """
    <script type="text/javascript" language="JavaScript"><!--
    function tag(s) { return '<'+s+'>'; }
    function popup_repr(title, value) {
        w = window.open('', '_blank',
            'directories=no,height=240,width=480,location=no,menubar=yes,'
            +'resizable=yes,scrollbars=yes,status=no,toolbar=no');
        if (!w) return true;
        w.document.open();
        w.document.write(tag('html')+tag('head')
            +tag('title')+title+tag('/title')+tag('/head')
            +tag('body style="background-color:#ffffff"')
            +tag('h3')+title+':'+tag('/h3')
            +tag('p')+tag('code')+value+tag('/code')+tag('/p')+tag('form')+
            tag('input type="button" onClick="window.close()" value="Close"')
            +tag('/form')+tag('/body')+tag('/html'));
        w.document.close();
        return false;
    }
    // -->
    </script>
    """

    traceback_summary = []

    for frame, file, lnum, func, lines, index in reversed(inspect_trace):
        if file:
            file = os.path.abspath(file)
        else:
            file = 'not found'
        traceback_summary.append('<a href="#%s:%d" style="%s">%s</a>:'
            '<code style="font-family:Courier,sans-serif">%s</code>'
            % (file.replace('/', '-').replace('\\', '-'), lnum,
                opt['header'], os.path.splitext(os.path.basename(file))[0],
                ("%5i" % lnum).replace(' ', '&nbsp;')))

    head = ('<table style="width:100%%;%s">'
        '<tr><td style="text-align:left;vertical-align:top">'
        '<strong style="font-size:x-large">%s</strong>: %s</td>'
        '<td rowspan="2" style="text-align:right;vertical-align:top">%s</td></tr>'
        '<tr><td style="vertical-align:top;background-color:#ffffff">\n'
        '<p style="%s">A problem occurred while running a Python script.</p>'
        '<p style="%s">Here is the sequence of function calls leading up to'
        ' the error, with the most recent (innermost) call first.</p>\n'
        '</td></tr></table>\n'
        % (opt['header'], etype, escape(str(evalue)),
        '<br>\n'.join(traceback_summary), opt['default'], opt['default']))

    indent = '<code><small>%s</small>&nbsp;</code>' % ('&nbsp;' * 5)
    traceback = []
    for frame, file, lnum, func, lines, index in reversed(inspect_trace):
        if file:
            file = os.path.abspath(file)
        else:
            file = 'not found'
        try:
            file_list = file.split('/')
            display_file = '/'.join(
                file_list[file_list.index('Webware') + 1:])
        except ValueError:
            display_file = file
        if display_file[-3:] == '.py':
            display_file = display_file[:-3]
        link = '<a id="%s:%d"></a><a href="file:%s">%s</a>' % (
            file.replace('/', '-').replace('\\', '-'),
            lnum, file.replace('\\', '/'), escape(display_file))
        args, varargs, varkw, locals = inspect.getargvalues(frame)
        if func == '?':
            call = ''
        else:
            call = 'in <strong>%s</strong>' % func + inspect.formatargvalues(
                args, varargs, varkw, locals,
                formatvalue=lambda value: '=' + html_repr(value))

        names = []
        dotted = [0, []]
        def tokeneater(type, token, start, end, line, names=names, dotted=dotted):
            if type == tokenize.OP and token == '.':
                dotted[0] = 1
            if type == tokenize.NAME and token not in keyword.kwlist:
                if dotted[0]:
                    dotted[0] = 0
                    dotted[1].append(token)
                    if token not in names:
                        names.append(dotted[1][:])
                elif token not in names:
                    if token != 'self':
                        names.append(token)
                    dotted[1] = [token]
            if type == tokenize.NEWLINE:
                raise IndexError
        def linereader(file=file, lnum=[lnum]):
            line = linecache.getline(file, lnum[0])
            lnum[0] += 1
            return line

        try:
            tokenize.tokenize(linereader, tokeneater)
        except IndexError:
            pass
        lvals = []
        for name in names:
            if isinstance(name, list):
                if name[0] in locals or name[0] in frame.f_globals:
                    name_list, name = name, name[0]
                    if name_list[0] in locals:
                        value = locals[name_list[0]]
                    else:
                        value = frame.f_globals[name_list[0]]
                        name = '<em>global</em> %s' % name
                    for subname in name_list[1:]:
                        if hasattr(value, subname):
                            value = getattr(value, subname)
                            name += '.' + subname
                        else:
                            name += '.' + '(unknown: %s)' % subname
                            break
                    name = '<strong>%s</strong>' % name
                    if isinstance(value, MethodType):
                        value = None
                    else:
                        value = html_repr(value)
            elif name in frame.f_code.co_varnames:
                if name in locals:
                    value = html_repr(locals[name])
                else:
                    value = '<em>undefined</em>'
                name = '<strong>%s</strong>' % name
            else:
                if name in frame.f_globals:
                    value = html_repr(frame.f_globals[name])
                else:
                    value = '<em>undefined</em>'
                name = '<em>global</em> <strong>%s</strong>' % name
            if value is not None:
                lvals.append('%s&nbsp;= %s' % (name, value))
        if lvals:
            lvals = ', '.join(lvals)
            lvals = indent + '<span style="%s">%s</span><br>\n' % (
                opt['code.unaccent'], lvals)
        else:
            lvals = ''

        level = ('<br><table style="width:100%%;%s">'
            '<tr><td>%s %s</td></tr></table>'
            % (opt['subheader'], link, call))
        excerpt = []
        try:
            i = lnum - index
        except TypeError:
            i = lnum
        lines = lines or ['file not found']
        for line in lines:
            number = '&nbsp;' * (5-len(str(i))) + str(i)
            number = '<span style="%s">%s</span>' % (
                opt['code.unaccent'], number)
            line = '<code>%s&nbsp;%s</code>' % (
                number, pyhtml.preformat(line))
            if i == lnum:
                line = ('<table style="width:100%%;%s">'
                    '<tr><td>%s</td></tr></table>'
                    % (opt['code.accent'], line))
            excerpt.append('\n' + line)
            if i == lnum:
                excerpt.append(lvals)
            i += 1
        traceback.append(level + '\n'.join(excerpt))

    exception = '<p><strong>%s</strong>: %s\n' % (etype, escape(str(evalue)))
    attribs = []
    if evalue is not None:
        for name in dir(evalue):
            if name.startswith('__'):
                continue
            value = html_repr(getattr(evalue, name))
            attribs.append('<br>%s%s&nbsp;= %s\n' % (indent, name, value))
    return (javascript + head + ''.join(traceback)
        + exception + ''.join(attribs) + '</p>\n')


def handler():
    print breaker()
    print html()


def html_repr(value):
    html_repr_instance = pyhtml._repr_instance
    enc_value = pyhtml.repr(value)
    if len(enc_value) > html_repr_instance.maxstring:
        plain_value = escape(repr(value))
        return ('%s <a href="#" onClick="return popup_repr('
            "'Full representation','%s')"
            '" title="Full representation">(complete)</a>' % (enc_value,
            escape(plain_value).replace("'", "\\'").replace('"', '&quot;')))
    else:
        return enc_value
