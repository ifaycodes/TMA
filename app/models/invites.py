from pydantic import EmailStr
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Invite(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr
    organisation_id: int = Field(foreign_key="organisation.id")
    inviter_id: int = Field(foreign_key="user.id")
    accepted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
