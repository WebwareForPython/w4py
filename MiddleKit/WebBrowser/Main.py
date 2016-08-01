from SitePage import SitePage


class Main(SitePage):

    def writeHTML(self):
        self.response().sendRedirect('SelectModel')
