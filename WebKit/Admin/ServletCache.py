import os
import time

from WebKit.URLParser import ServletFactoryManager
from WebUtils.Funcs import htmlEncode
from AdminSecurity import AdminSecurity


class ServletCache(AdminSecurity):
    """Display servlet cache.

    This servlet displays, in a readable form, the internal data
    structure of the cache of all servlet factories.

    This can be useful for debugging WebKit problems and the
    information is interesting in general.
    """

    def title(self):
        return 'Servlet Cache'

    def writeContent(self):
        wr = self.writeln
        factories = [factory for factory in ServletFactoryManager._factories
            if factory._classCache]
        if not factories:
            wr('<h4>No caching servlet factories found.</h4>')
            wr('<p>Caching can be activated by setting'
                ' <code>CacheServletClasses = True</code>.</p>')
            return
        if len(factories) > 1:
            factories.sort()
            wr('<h3>Servlet Factories:</h3>')
            wr('<table>')
            for factory in factories:
                wr('<tr><td><a href="#%s">%s</a></td></tr>'
                    % ((factory.name(),)*2))
            wr('</table>')
        req = self.request()
        wr('<form action="ServletCache" method="post">')
        for factory in factories:
            name = factory.name()
            wr('<a id="%s"></a><h4>%s</h4>' % ((name,)*2))
            if req.hasField('flush_' + name):
                factory.flushCache()
                wr('<p style="color:green">'
                    'The servlet cache has been flushed. &nbsp; '
                    '<input type="submit" name="reload" value="Reload"></p>')
                continue
            wr(htCache(factory))
        wr('</form>')

def htCache(factory):
    """Output the cache of a servlet factory."""
    html = []
    wr = html.append
    cache = factory._classCache
    keys = sorted(cache)
    wr('<p>Uniqueness: %s</p>' % factory.uniqueness())
    wr('<p>Extensions: %s</p>' % ', '.join(map(repr, factory.extensions())))
    wr('<p>Unique paths in the servlet cache: <strong>%d</strong>'
        ' &nbsp; <input type="submit" name="flush_%s" value="Flush"></p>'
        % (len(keys), factory.name()))
    wr('<p>Click any link to jump to the details for that path.</p>')
    wr('<h5>Filenames:</h5>')
    wr('<table class="NiceTable">')
    wr('<tr><th>File</th><th>Directory</th></tr>')
    paths = []
    for key in keys:
        dir, base = os.path.split(key)
        path = dict(dir=dir, base=base, full=key)
        paths.append(path)
    paths.sort(key=lambda path: (path['base'].lower(), path['dir'].lower()))
    # At this point, paths is a list where each element is a tuple
    # of (basename, dirname, fullPathname) sorted first by basename
    # and second by dirname
    for path in paths:
        wr('<tr><td><a href="#id%s">%s</a></td><td>%s</td></tr>'
            % (id(path['full']), path['base'], path['dir']))
    wr('</table>')
    wr('<h5>Full paths:</h5>')
    wr('<table class="NiceTable">')
    wr('<tr><th>Servlet path</th></tr>')
    for key in keys:
        wr('<tr><td><a href="#%s">%s</a></td></tr>' % (id(key), key))
    wr('</table>')
    wr('<h5>Details:</h5>')
    wr('<table class="NiceTable">')
    for path in paths:
        wr('<tr class="NoTable"><td colspan="2">'
            '<a id="id%s"></a><strong>%s</strong> - %s</td></tr>'
            % (id(path['full']), path['base'], path['dir']))
        record = cache[path['full']].copy()
        record['path'] = path['full']
        if path['full'] in factory._threadsafeServletCache:
            record['instances'] = 'one servlet instance (threadsafe)'
        else:
            record['instances'] = ('free reusable servlets: %d'
                % len(factory._servletPool))
        wr(htRecord(record))
    wr('</table>')
    return '\n'.join(html)

def htRecord(record):
    html = []
    wr = html.append
    for key in sorted(record):
        htKey = htmlEncode(key)
        # determine the HTML for the value
        value = record[key]
        htValue = None
        # check for special cases where we want a custom display
        if hasattr(value, '__name__'):
            htValue = value.__name__
        if key == 'mtime':
            htValue = '%s (%s)' % (time.asctime(time.localtime(value)), value)
        # the general case:
        if not htValue:
            htValue = htmlEncode(str(value))
        wr('<tr><th>%s</th><td>%s</td></tr>' % (htKey, htValue))
    return '\n'.join(html)
