from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Chat(BaseModel):
    """Chat data model for Bigtable storage"""
    id: str
    title: str
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ChatSchema(BaseModel):
    id: str
    title: str
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ChatCreate(BaseModel):
    title: str
    user_id: int

class ChatMessage(BaseModel):
    """Chat message data model for Bigtable storage"""
    id: int
    chat_id: str
    user_id: int
    message_type: str  # 'user' or 'assistant'
    content: str  # Either prompt or response content
    tokens_used: Optional[int] = None
    model: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChatMessageSchema(BaseModel):
    id: int
    chat_id: str
    user_id: int
    message_type: str
    content: str
    tokens_used: Optional[int] = None
    model: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChatMessageCreate(BaseModel):
    chat_id: str
    user_id: int
    message_type: str
    content: str
    tokens_used: Optional[int] = None
    model: Optional[str] = None