"""
AI interface extension
"""
from typing import override, Optional
from pyjolt import Request
from pyjolt.ai_interface import AiInterface, tool
from app.api.models import ChatSession

class Interface(AiInterface):

    @override
    async def chat_session_loader(self, req: Request) -> Optional[ChatSession]:
        print("Loading chat session: ", req.route_parameters)
        return ChatSession()

    @tool(description="Returns weather for provided location")    
    async def weather_widget(self, location: str):
        """AI tool method"""
        return f"Weather at {location} is nice!"

ai_interface: Interface = Interface()
