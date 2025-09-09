"""
Users API
"""

from pyjolt import Controller, path, get, Request, Response

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
    async def get_user(self, req: Request, user_id: int) -> Response:
        """Returns single user"""
        print(self.app)
        return req.response.json({
            "message": "User fetched successfully",
            "status": "success",
            "data": {
                "user_id": user_id
            }
        }).status(200)
