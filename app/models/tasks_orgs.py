from sqlmodel import SQLModel, Field
from typing import Optional

class TaskOrganisation(SQLModel, table=True):
    task_id: Optional[int] = Field(default=None, foreign_key="task.id", primary_key=True)
    organisation_id: Optional[int] = Field(default=None, foreign_key="organisation.id", primary_key=True)
