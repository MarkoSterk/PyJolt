"""
AI Interface
"""
from typing import Optional

from app.api.models.chat_session import ChatSession
from app.extensions import db

from pyjolt.database import AsyncSession
from pyjolt.ai_interface import AiInterface
from pyjolt.request import Request


class Interface(AiInterface):

    @db.managed_session
    #pylint: disable-next=W0221
    async def chat_context_loader(self, req: Request,
                                  session: AsyncSession) -> Optional[ChatSession]:
        chat_session_id: Optional[int] = req.route_parameters.get("chat_session_id",
                                                                  None)
        if chat_session_id is None:
            return None
        return await ChatSession.query(session).filter_by(id = chat_session_id).first()

ai_interface: Interface = Interface()
