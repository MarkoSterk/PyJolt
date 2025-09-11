"""
Users API
"""
from pyjolt import Request, Response
from pyjolt.controller import Controller, path, get, consumes, produces, MediaType

@path("/<string:lang>/api/v1/users")
class UsersApi(Controller):

    @get("/")
    async def get_users(self, req: Request, lang: str) -> Response:
        """Endpoint for returning all app users"""
        return req.response.json({
            "message": "All users fetched",
            "status": "success",
            "data": None
        }).status(200)
    
    @get("/<int:user_id>")
    @produces(MediaType.application_json)
    async def get_user(self, req: Request, lang: str, user_id: int) -> Response:
        """Returns single user by id"""
        return req.response.json({
            "message": "User fetched successfully",
            "status": "success",
            "data": {
                "url_for": self.app.url_for("StaticController.static", filename="board_test.jpg"),
                "user_id": user_id
            }
        }).status(200)
    
    @get("/hello")
    @produces(MediaType.text_html)
    async def hello_user(self, req: Request, lang: str) -> Response:
        """Hello world for user"""
        return await req.res.html("index.html", {"language": lang})

    @post("/")
    @consumes(MediaType.application_json)
    @produces(MediaType.application_json)
    async def post_test(self, req: Request, data: TestPydanticModel) -> Response:
        """Consumes json"""
        #SOME LOGIC