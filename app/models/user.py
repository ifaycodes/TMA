from sqlmodel import Field, SQLModel, Relationship
from typing import Optional
from app.models.organisations import UserOrganisation


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    password: str
    email: str = Field(index=True, unique=True)
    active_org_id: Optional[int] = Field(default=None, foreign_key="organisation.id")

    organisations: list[UserOrganisation] = Relationship(back_populates="user")
    created_organizations: list["Organisation"] = Relationship(back_populates="creator")
