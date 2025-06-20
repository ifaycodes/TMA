from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from app.models.tasks_orgs import TaskOrganisation

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    completed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    organization_id: Optional[int] = Field(foreign_key="organisation.id")
    organisations: list["Organisation"] = Relationship(
        back_populates="tasks",
        link_model=TaskOrganisation
    )
