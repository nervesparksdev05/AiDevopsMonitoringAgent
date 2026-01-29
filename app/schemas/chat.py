from typing import Optional, Dict
from pydantic import BaseModel

class ChatMessage(BaseModel):
    message: str
    context: Dict = {}
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
