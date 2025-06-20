from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import get_current_user, get_session
from app.models.task import Task
from app.models.tasks_orgs import TaskOrganisation
from app.models.user import User
from app.models.organisations import UserOrganisation

from sqlmodel import Session, select

from app.db.session import get_session
from app.schemas.user import TaskRead, TaskCreate

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/create", response_model=TaskRead)
def create_task(
        task_data: TaskCreate,
        session: Session = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    #org_id = current_user.org_id if task_data.in_organisation else None
    task = Task(
        title=task_data.title,
        description=task_data.description,
        #organisation_id=org_id
    )

    session.add(task)
    session.commit()
    session.refresh(task)

    if task_data.organisation_id:
        for org_id in task_data.organisation_id:
            link = TaskOrganisation(task_id=task.id, organisation_id=org_id)
            session.add(link)

    session.commit()
    return task

@router.patch("/update", response_model=TaskRead)
def assign_task_to_org(
        id: int,
        session: Session = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    task = session.get(Task, id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if not current_user.active_org_id:
        raise HTTPException(status_code=403, detail="Not active org to set to")

    # Check if the task is already linked to this org
    stmt = select(TaskOrganisation).where(TaskOrganisation.task_id == id,
        TaskOrganisation.organisation_id == current_user.active_org_id
    )
    existing_link = session.exec(stmt).first()

    if existing_link:
        raise HTTPException(status_code=400, detail="Task already assigned to this organisation")

    #Add link
    link = TaskOrganisation(task_id=id, organisation_id=current_user.active_org_id)
    session.add(link)
    session.commit()
    session.refresh(task)
    return task

@router.get("/org", response_model=list[TaskRead])
def get_tasks(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if not current_user.active_org_id:
        raise HTTPException(status_code=400, detail="No active organisation set")

    stmt = (
        select(Task)
        .join(TaskOrganisation)
        .where(TaskOrganisation.organisation_id == current_user.active_org_id)
    )

    tasks = session.exec(stmt).all()
    return tasks

@router.get("/personal", response_model=list[TaskRead])
def get_personal_tasks(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    stmt = (
        select(Task)
        .where(~Task.id.in_(select(TaskOrganisation.task_id)
        ))
    )

    tasks = session.exec(stmt).all()
    return tasks

@router.get("/all", response_model=list[TaskRead])
def get_all_user_tasks(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    #get all orgs the user belongs to
    stmt_user_orgs = select(UserOrganisation.organisation_id).where(
        UserOrganisation.user_id == current_user.id
    )
    user_org_ids = [org_id for org_id, in session.exec(stmt_user_orgs).all()]

    #get all task IDs linked to the orgs
    stmt_task_ids = select(TaskOrganisation.task_id).where(
        TaskOrganisation.organisation_id.in_(user_org_ids)
    )
    org_task_ids = [task_id for task_id, in session.exec(stmt_task_ids).all()]

    #get all org-linked tasks + personal tasks
    stmt = select(Task).where(
        (Task.id.in_(org_task_ids)) |
        (~Task.id.in_(select(TaskOrganisation.task_id)))
    )

    tasks = session.exec(stmt).all()
    return tasks
