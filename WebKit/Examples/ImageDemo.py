from math import sin, pi

from MiscUtils import StringIO
from MiscUtils.Funcs import asclocaltime
from ExamplePage import ExamplePage

try:  # GD module
    from gd import image as gdImage, gdFontLarge
except ImportError:
    gdImage = None
    try:  # Python Imaging Library
        import Image as pilImage, ImageDraw, ImageFont
    except ImportError:
        try:
            from PIL import Image as pilImage, ImageDraw, ImageFont
        except ImportError:
            pilImage = None

def image_lib_link(lib=None):
    if not lib:
        lib = 'gd' if gdImage else 'pil'
    name, src = dict(
        gd = ('GD module',
            'newcenturycomputers.net/projects/gdmodule.html'),
        pil = ('Python Imaging Library (PIL)',
            'www.pythonware.com/products/pil/'))[lib]
    return '<a href="http://%s">%s</a>' % (src, name)

X, Y = 500, 200  # the image size

def t(p):
    """Map coordinates: (x=0..2pi, y=-1.25..1.25) => (0..X, Y..0)"""
    return int(.5*X*p[0]/pi+.5), int(.4*Y*(1.25- p[1])+.5)

colors = (255, 255, 255), (0, 0, 0), (0, 0, 255), (255, 0, 0)
white, black, blue, red = range(4)


class Drawing(object):
    """Simple wrapper class for drawing the example image."""

    if gdImage:

        def __init__(self):
            self._image = gdImage((X, Y))
            self._color = map(self._image.colorAllocate, colors)
            self._font = gdFontLarge

        def text(self, pos, string, color):
            color = self._color[color]
            self._image.string(self._font, t(pos), string, color)

        def lines(self, points, color):
            color = self._color[color]
            self._image.lines(map(t, points), color)

        def png(self):
            s = StringIO()
            self._image.writePng(s)
            return s.getvalue()

    else:

        def __init__(self):
            self._image = pilImage.new('RGB', (X, Y), colors[white])
            self._draw = ImageDraw.Draw(self._image)
            for font in 'Tahoma Verdana Arial Helvetica'.split():
                try:
                    font = ImageFont.truetype(font + '.ttf', 12)
                except (AttributeError, IOError):
                    font = None
                if font:
                    break
            else:
                try:
                    font = ImageFont.load_default()
                except (AttributeError, IOError):
                    font = None
            self._font = font

        def text(self, pos, string, color):
            color = colors[color]
            self._draw.text(t(pos), string, color, font=self._font)

        def lines(self, points, color):
            color = colors[color]
            self._draw.line(map(t, points), color)

        def png(self):
            s = StringIO()
            self._image.save(s, 'png')
            return s.getvalue()


class ImageDemo(ExamplePage):
    """Dynamic image generation example.

    This example creates an image of a sinusoid.

    For more information on generating graphics, see
    http://python.org/topics/web/graphics.html.

    This example works with both PIL and GD.
    """

    def defaultAction(self):
        if self.request().field('fmt', None) == '.png' and (gdImage or pilImage):
            image = self.generatePNGImage()
            res = self.response()
            res.setHeader("Content-Type", "image/png")
            res.setHeader("Content-Length", str(len(image)))
            # Uncomment the following line to suggest to the client that the
            # result should be saved to a file, rather than displayed in-line:
            # res.setHeader("Content-Disposition", "attachment; filename=foo.png")
            self.write(image)
        else:
            self.writeHTML()

    def writeContent(self):
        wr = self.writeln
        wr('<h2>WebKit Image Generation Demo</h2>')
        if gdImage or pilImage:
            wr('<img src="ImageDemo?fmt=.png" alt="Generated example image"'
                ' width="%d" height="%d">' % (X, Y))
            wr('<p>This image has just been generated using the %s.</p>' %
                image_lib_link())
        else:
            wr('<h4 style="color:red">Sorry: No image library available.</h4>')
            wr('<p>This example requires the %s.</p>' % ' or the '.join(
                map(image_lib_link, ('gd', 'pil'))))

    def generatePNGImage(self):
        """Generate and return a PNG example image."""
        def f(x):
            return x, sin(x)
        draw = Drawing()
        draw.text((2.7, 0.8), 'y=sin(x)', black)
        draw.text((0.2, -0.8), 'created: ' + asclocaltime(), red)
        draw.lines(((0, 0), (2*pi, 0)), black)  # x-axis
        draw.lines(((0, -1), (0, 1)), black)  # y-axis
        draw.lines(map(f, map(lambda x: x*2*pi/X, xrange(X+1))), blue)
        return draw.png()
