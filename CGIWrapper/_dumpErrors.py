"""CGIWrapper dump errors admin script."""

from WebUtils.Funcs import htmlEncode
from _dumpCSV import _dumpCSV


class _dumpErrors(_dumpCSV):

    def cellContents(self, rowIndex, colIndex, value):
        """Return cell contents of CSV file.

        This subclass adds a link to error files.
        """
        if self._headings[colIndex] == 'error report filename':
            return '<a href="_viewError?filename=%s">%s</a>' % (value, value)
        else:
            return htmlEncode(value)
