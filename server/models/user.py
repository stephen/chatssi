from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class User(BaseModel):
    """User data model for Bigtable storage"""
    id: int
    name: str
    email: str
    google_id: str
    picture: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserSchema(BaseModel):
    id: int
    name: str
    email: str
    google_id: str
    picture: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    name: str
    email: str
    google_id: str
    picture: Optional[str] = None