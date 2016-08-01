# PSP
# Webware for Python
# See Docs/index.html

from PSPServletFactory import PSPServletFactory

def InstallInWebKit(appServer):
    app = appServer.application()
    app.addServletFactory(PSPServletFactory(app))
