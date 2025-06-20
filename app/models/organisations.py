from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from app.models.tasks_orgs import TaskOrganisation

class Organisation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    creator_id: int = Field(foreign_key="user.id")
    creator: Optional["User"] = Relationship(back_populates="created_organisations")
    users: List["UserOrganisation"] = Relationship(back_populates="organisation")

class UserOrganisation(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    organisation_id: int = Field(foreign_key="organisation.id", primary_key=True)
    role: str = Field(default="member")
    user: "User" = Relationship(back_populates="organisations")
    organisation: "Organisation" = Relationship(back_populates="users")

    tasks: list["Task"] = Relationship(
        back_populates="organisations",
        link_model=TaskOrganisation
)

if TYPE_CHECKING:
    from .user import User