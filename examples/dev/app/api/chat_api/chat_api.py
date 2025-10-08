"""
Chat API
"""
from pyjolt import Request, Response, HttpStatus, MediaType
from pyjolt.controller import Controller, get, path, produces

@path("/api/v1/chat")
class ChatApi(Controller):

    @get("/<int:chat_session_id>")
    @produces(MediaType.APPLICATION_JSON)
    async def get_chat_session(self, req: Request, chat_session_id: int) -> Response:

        return req.res.json({
            "chat_session_id": chat_session_id
        }).status(HttpStatus.OK)
