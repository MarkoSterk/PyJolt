"""
Data transfer object for ChatAPI
"""
from pydantic import BaseModel, Field

class ChatPrompt(BaseModel):
    
    prompt: str = Field(min_length=10, max_length=500)

class ChatResponse(BaseModel):
    
    message: str
    status: str
    data: str|None = None