import os
from operator import itemgetter
from stat import ST_SIZE

print '''%s
<html>
    <head>
        <title>Webware CGI Examples Directory</title>
    </head>
    <body>
        <h1 style="text-align:center">Webware CGI Examples</h1>
''' % wrapper.docType()

# Create a list of dictionaries, where each dictionary stores information about
# a particular script.
scripts = sorted((dict(pathname=filename,
    shortname=filename[:-3], size=os.stat(filename)[ST_SIZE])
    for filename in os.listdir(os.curdir)
    if len(filename) > 3 and filename.endswith('.py')),
    key=itemgetter('size'))


print '''\
        <table style="margin-left:auto;margin-right:auto">
            <tr>
                <th style="text-align:right">Size</th>
                <th style="text-align:right">Script</th>
                <th style="text-align:right">View</th>
            </tr>'''

for script in scripts:
    print '''\
            <tr>
                <td align=right>%(size)d</td>
                <td><a href="%(shortname)s">%(shortname)s</a></td>
                <td><a href="View?filename=%(shortname)s">view</a></td>
            </tr>''' % script

print '''\
        </table>
    </body>
</html>'''
