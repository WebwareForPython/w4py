
print '''%s
<html>
<head><title>FormTest</title></head>
<body>
<h1>Form Test</h1>
<form action="FormTest">
<input type="text" name="text">
<input name="button" type="submit" value="Submit">
</form>
<p>
fields = %s
</p>
</html>
''' % (wrapper.docType(), fields)
