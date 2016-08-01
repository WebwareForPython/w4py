
print '''%s
<html>
    <head>
        <title>Hello, word!</title>
    </head>
    <body>
        <h1 align="center">Hello, World!</h1>
        <p align="center">This is CGI Wrapper %s speaking...</p>
    </body>
</html>''' % (wrapper.docType(), wrapper.version())
