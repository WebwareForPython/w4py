<?xml version='1.0' encoding='utf-8'?>
<?python
title = "The Mandelbrot Set"
def color(x,y):
    z = c = complex(x, -y)/100.0
    for n in range(16):
        z = z*z + c
        if abs(z) > 2:
            break
    return "#%x82040" % n
?>
<html xmlns="http://www.w3.org/1999/xhtml"
  xmlns:py="http://purl.org/kid/ns#">
<head>
<title py:content="title"/>
<style type="text/css">
body {color:black; background-color:white; }
h1 { text-align: center; font-family: sans-serif; }
table { margin: 1ex auto; empty-cells: show;
border-collapse: separate; border-spacing: 1px; border-style: none; }
table td { padding: 3px; }
</style>
</head>
<body>
<h1 py:content="title"/>
<table>
    <tr py:for="y in range(-150, 150, 5)">
        <td py:for="x in range(-250, 100, 5)" style="background-color:${color(x,y)}"/>
    </tr>
</table>
</body>
</html>
