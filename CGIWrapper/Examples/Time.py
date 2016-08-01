
import time

print '''%s
<html>
    <head>
        <title>Time</title>
    </head>
    <body>
    <h3>Current Time</h3>
    <p>%s</p>
    </body>
</html>''' % (wrapper.docType(), time.asctime(time.localtime()))
