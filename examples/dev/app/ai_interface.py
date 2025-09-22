"""
AI interface extension
"""
from typing import override, Optional, TYPE_CHECKING
from pyjolt import Request
from pyjolt.ai_interface import AiInterface, tool

if TYPE_CHECKING:
    from app.api.models import ChatSession

class Interface(AiInterface):

    @override
    async def chat_session_loader(self, req: Request) -> "Optional[ChatSession]":
        #Lazy loading model to avoid circular imports
        from app.api.models import ChatSession
        print("Loading chat session: ", req.route_parameters)
        return None#ChatSession()

    @tool(description="Returns weather for provided location")    
    async def weather_widget(self, location: str):
        """AI tool method"""
        return f"Weather at {location} is nice!"
