
print '''%s
<html>
    <head>
        <title>Hello, word!</title>
    </head>
    <body>
        <h1 style="text-align:center">Hello, World!</h1>
        <p style="text-align:center">This is CGI Wrapper %s speaking...</p>
    </body>
</html>''' % (wrapper.docType(), wrapper.version())
