"""
Chat API
"""
from pyjolt import Request, Response, HttpStatus, MediaType
from pyjolt.controller import Controller, get, path, produces
from app.authentication import auth

@path("/api/v1/chat")
#@auth.login_required
class ChatApi(Controller):

    @get("/<int:chat_session_id>")
    @produces(MediaType.APPLICATION_JSON)
    @auth.login_required
    async def get_chat_session(self, req: Request, chat_session_id: int) -> Response:

        return req.res.json({
            "chat_session_id": chat_session_id
        }).status(HttpStatus.OK)
