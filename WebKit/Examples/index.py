from WebKit.HTTPServlet import HTTPServlet


class index(HTTPServlet):

    def respond(self, trans):
        extraPath = trans.request().extraURLPath()
        path = trans.request().urlPath()
        if path.endswith(extraPath):
            path = path[:-len(extraPath)]
        if not path.endswith('Welcome'):
            path = path.rpartition('/')[0] + '/Welcome' + extraPath
            # redirection via the server:
            trans.application().forward(trans, path)
            # redirection via the client:
            # trans.response().sendRedirect(path)
