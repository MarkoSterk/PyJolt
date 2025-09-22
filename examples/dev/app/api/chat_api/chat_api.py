"""
Chat API
"""
from pyjolt import Request, Response, MediaType, HttpStatus
from pyjolt.controller import Controller, path, post, consumes, produces

from app.authentication import auth
from app.ai_interface import ai_interface
from app.api.models import ChatSession

from app.api.chat_api.dtos import ChatPrompt, ChatResponse


@path("/api/v1/chat")
class ChatAPI(Controller):
    
    @post("/session/<int:session_id>")
    @consumes(MediaType.APPLICATION_JSON)
    @produces(MediaType.APPLICATION_JSON)
    @ai_interface.with_chat_session
    @auth.login_required
    async def chat_prompt(self, req: Request,
                          session_id: int,
                          prompt: ChatPrompt,
                          chat_session: ChatSession) -> Response[ChatResponse]:
        """
        Make prompt to OpenAI
        """
        print("Received prompt: ", prompt.prompt)
        print("Injected session: ", chat_session)
        print("Making new prompt in chat session ", session_id)
        
        ##Prompt to OpenAI or other LLM logic
        
        return req.response.json({
                "message": "Prompt successful",
                "status": "success"
            }).status(HttpStatus.OK)
        