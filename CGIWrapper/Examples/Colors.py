
if 'bgcolor' in fields:
    bgcolor = fields['bgcolor'].value
    bgcolorArg = 'style="background-color=%s"' % bgcolor
else:
    bgcolor = ''
    bgcolorArg = ''

print '''<!DOCTYPE html>
<html>
    <head>
        <title>Colors</title>
    </head>
    <body %s>
        <h1 style="text-align:center">Colors</h1>
        <center>
        <form action="Colors">
            bgcolor: <input type="text" name="bgcolor" value="%s">
            <input type="submit" value="Go">
        </form>
        <table>
''' % (bgcolorArg, bgcolor)

space = '&nbsp;'*10
gamma = 2.2  # an approximation for today's CRTs, see "brightness =" below

for r in range(11):
    r /= 10.0
    for g in range(11):
        g /= 10.0
        print '<tr>'
        for b in range(11):
            b /= 10.0
            color = '#%02x%02x%02x' % (r*255, g*255, b*255)
            # Compute brightness given RGB
            brightness = (0.3*r**gamma + 0.6*g**gamma + 0.1*b**gamma)**(1/gamma)
            # We then use brightness to determine a good font color for high contrast
            textcolor = 'white' if brightness < 0.5 else 'black'
            print '<td style="color:%s;background-color:%s;">%s</td>' % (textcolor, color, color)
        print '</tr>'

print '''
        </table>
        </center>
    </body>
</html>'''
