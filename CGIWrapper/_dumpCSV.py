"""CGIWrapper dump CSV admin script."""

import os

from WebUtils.Funcs import htmlEncode
from AdminPage import AdminPage


def LoadCSV(filename):
    """Load CSV file.

    Loads a CSV (comma-separated value) file from disk and returns it as a
    list of rows where each row is a list of values (which are always strings).
    """
    try:
        with open(filename) as f:
            rows = []
            while 1:
                line = f.readline()
                if not line:
                    break
                rows.append(line.split(','))
    except IOError:
        rows = []
    return rows


class _dumpCSV(AdminPage):
    """CGIWrapper class that dumps a CSV file."""

    def __init__(self, dict):
        AdminPage.__init__(self, dict)
        self._filename = self._fields['filename'].value

    def shortFilename(self):
        return os.path.splitext(os.path.split(self._filename)[1])[0]

    def title(self):
        return 'View ' + self.shortFilename()

    def writeBody(self):
        rows = LoadCSV(self._filename)

        self.writeln('<table style="margin-left:auto;margin-right:auto">')

        # Head row gets special formatting
        self._headings = map(lambda name: name.strip(), rows[0])
        self.writeln('<tr>')
        for value in self._headings:
            self.writeln('<th style="color:white;background-color:#101040;'
                'font-family:Arial,Helvetica,sans-serif">',
            value, '</th>')
        self.writeln('</tr>')

        # Data rows
        rowIndex = 1
        for row in rows[1:]:
            self.writeln('<tr>')
            colIndex = 0
            for value in row:
                self.writeln(
                    '<td style="color:#111111;background-color:#EEEEEE">',
                    self.cellContents(rowIndex, colIndex, value), '</td>')
                colIndex += 1
            self.writeln('</tr>')
            rowIndex += 1

        self.writeln('</table>')

    def cellContents(self, rowIndex, colIndex, value):
        """Return cell contents of CSV file.

        This is a hook for subclasses to customize the contents of a cell
        based on any criteria (including location).
        """
        return htmlEncode(value)
