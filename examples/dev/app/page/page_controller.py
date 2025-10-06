"""
Page controller example - for returning HTML pages
"""
from pyjolt.controller import Controller, get, path, produces
from pyjolt import MediaType, Request, Response

@path("/", open_api_spec=False) #not included in open api specs
class PageController(Controller):
    """
    Example controller for returning HTML pages
    """

    @get("/")
    @produces(MediaType.TEXT_HTML)
    async def index(self, req: Request) -> Response:
        """
        Example index page
        """
        #Context that is injected into the template
        context: dict = {
            "user": "John Doe"
        }
        return await req.res.html("index.html", context)

    @get("/about")
    @produces(MediaType.TEXT_HTML)
    async def about(self, req: Request) -> Response:
        """
        Example about page
        """
        context: dict = {
            "company": {
                "name": "My Company",
                "address": "1234 Main St, Anytown, USA"
            }
        }
        return await req.res.html("about.html", context)
        