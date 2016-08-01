"""CGIWrapper access denied script."""

headers['status'] = "403 Forbidden"

print '''%s
<html>
    <head>
        <title>Access denied</title>
    </head>
    <body>
        <h1>Access denied</h1>
    </body>
</html>''' % wrapper.docType()
