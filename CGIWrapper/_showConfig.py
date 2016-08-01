from CGIWrapper import htDictionary
from AdminPage import AdminPage


class _showConfig(AdminPage):

    def title(self):
        return 'Config'

    def writeBody(self):
        self.writeln(htDictionary(self._wrapper.config()))
