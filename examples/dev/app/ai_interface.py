"""
AI interface extension
"""
from typing import override
from pyjolt import Request
from pyjolt.ai_interface import AiInterface

from app.api.models import ChatSession

class Interface(AiInterface):

    @override
    async def chat_session_loader(self, req: Request) -> ChatSession:
        print("Loading chat session: ", req.route_parameters)
        return None
