import os

print '''%s
<html>
    <head>
        <title>Webware View CGI Source</title>
    </head>
    <body>
        <h1>Webware View CGI Source</h1>
''' % wrapper.docType()

if 'filename' not in fields:
    print '<p>No filename specified.</p>'
else:
    if 'tabSize' in fields:
        tabSize = int(fields['tabSize'].value)
    else:
        tabSize = 4
    filename = os.path.basename(fields['filename'].value)
    if not filename.endswith('.py'):
        fielname += '.py'
    try:
        contents = open(filename).read()
    except IOError:
        contents = '(cannot view file)'
    if tabSize > 0:
        contents = contents.expandtabs(tabSize)
    contents = contents.replace('&', '&amp;')
    contents = contents.replace('<', '&lt;')
    contents = contents.replace('>', '&gt;')
    print '<h2>%s</h2><hr><pre>%s</pre>' % (filename, contents)

print '''
    </body>
</html>'''
