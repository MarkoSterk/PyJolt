"""
Users API
"""
from pyjolt import Request, Response
from pyjolt.controller import Controller, path, get, consumes, produces, MediaType

@path("/api/v1/users")
class UsersApi(Controller):

    @get("/")
    async def get_users(self, req: Request) -> Response:
        """Endpoint for returning all app users"""
        return req.response.json({
            "message": "All users fetched",
            "status": "success",
            "data": None
        }).status(200)
    
    @get("/<int:user_id>")
    @produces(MediaType.application_json, MediaType.text_html)
    async def get_user(self, req: Request, user_id: int) -> Response:
        """Returns single user by id"""
        return req.response.json({
            "message": "User fetched successfully",
            "status": "success",
            "data": {
                "user_id": user_id
            }
        }).status(200)
