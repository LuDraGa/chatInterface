from typing import List, Optional, Literal
from pydantic import BaseModel, HttpUrl
# from chainlit.message import Message

class Message(BaseModel):
    role: Literal["system", "assistant", "user"]
    content: str
    # image_url: Optional[HttpUrl] = None
    # image_path: Optional[str] = None

class AgentProfile(BaseModel):
    name: str
    description: str
    message_list: List[Message]
    tools_list: Optional[List[str]] = None
    modality_list: Optional[List[str]] = None
