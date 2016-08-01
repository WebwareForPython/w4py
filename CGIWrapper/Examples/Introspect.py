
print '''%s
<html>
    <head>
        <title>Python Introspection</title>
    </head>
    <body>
        <h2>Basic Python Introspection</h2>
''' % wrapper.docType()

def printKeys(name, obj):
    print '<p> <b>%s</b> = %s' % (name, ', '.join(sorted(obj)))

printKeys('globals', globals())
printKeys('locals', locals())
printKeys('environ', environ)
printKeys('fields', fields)
printKeys('headers', headers)
printKeys('wrapper.__dict__', wrapper.__dict__)

print '''
        <hr>
        <p>Note that the <a href="Error">Error</a> script
        results in a much better display of introspection.</p>
    </body>
</html>'''
