"""
AI interface extension
"""
from typing import override, TYPE_CHECKING, Optional
from pyjolt import Request
from pyjolt.ai_interface import AiInterface

if TYPE_CHECKING:
    from app.api.models import ChatSession

class Interface(AiInterface):

    @override
    async def chat_session_loader(self, req: Request) -> "Optional[ChatSession]":
        print("Loading chat session: ", req.route_parameters)
        return None
