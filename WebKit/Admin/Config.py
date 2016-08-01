from AdminSecurity import AdminSecurity
from WebUtils.Funcs import htmlForDict


class Config(AdminSecurity):

    def title(self):
        return 'Config'

    def writeContent(self):
        self.writeln(htmlForDict(self.application().server().config(),
            topHeading='AppServer'))
        self.writeln(htmlForDict(self.application().config(),
            topHeading='Application'))
