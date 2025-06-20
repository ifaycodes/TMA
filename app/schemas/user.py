from pydantic import  BaseModel, EmailStr
from sqlmodel import SQLModel
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    name: str
    password: str
    email: EmailStr

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class OrganisationCreate(BaseModel):
    name: str

class OrganisationRead(BaseModel):
    id:int
    name: str

    class Config:
        from_attributes = True

class OrganisationWithCreator(SQLModel):
    id: int
    name: str
    creator_name: str

    class Config:
        from_attributes=True


class InviteUserRequest(BaseModel):
    email: EmailStr

class PromoteUserRequest(BaseModel):
    email: str
    role: str

class TaskCreate(SQLModel):
    title: str
    description: Optional[str] = None
    organisation_id: Optional[list[int]] = None

class TaskRead(SQLModel):
    id: int
    title: str
    description: Optional[str]
    completed: bool
    created_at: datetime

    class Config:
        from_attributes=True
