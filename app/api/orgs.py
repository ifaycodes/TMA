from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import  Session, select
from app.models.invites import Invite
from app.models.organisations import Organisation, UserOrganisation
from app.models.user import User
from app.db.session import get_session
from app.auth.dependencies import get_current_user
from app.schemas.user import OrganisationCreate, OrganisationRead, InviteUserRequest, PromoteUserRequest, OrganisationWithCreator

router = APIRouter(prefix="/organisations", tags=["organisations"])
@router.post("/Create", response_model=OrganisationRead)
def create_organisation(
        org_data: OrganisationCreate,
        session: Session = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    #Create a new org
    org = Organisation(name=org_data.name, creator_id=current_user.id)
    session.add(org)
    session.commit()
    session.refresh(org)

    #link to a user
    link = UserOrganisation(user_id=current_user.id, organisation_id=org.id, role="owner")
    session.add(link)

    #set as active org
    current_user.active_org_id = org.id

    session.commit()
    return org

@router.get("/Owned", response_model=list[OrganisationRead])
def get_owned_organisations(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Organisation).join(UserOrganisation).where(
        (UserOrganisation.user_id == current_user.id) &
        (UserOrganisation.role == "owner")
    )
    orgs = session.exec(stmt).all()
    return orgs

@router.get("/Belongto", response_model=list[OrganisationWithCreator])
def get_belong_to_organisations(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Organisation).join(UserOrganisation).where(
        (UserOrganisation.user_id == current_user.id) &
        (UserOrganisation.role.in_(["member", "admin"]))
    )
    orgs = session.exec(stmt).all()
    result = [
        OrganisationWithCreator(
            id=org.id,
            name=org.name,
            creator_name=org.creator.name if org.creator else "Unknown"
        )
        for org in orgs
    ]
    return result


@router.patch("/switch")
def switch_active_organisation(org_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    #check if user is in org
    stmt = select(UserOrganisation).where((UserOrganisation.user_id == current_user.id) & (UserOrganisation.organisation_id == org_id))

    link = session.exec(stmt).first()

    if not link:
        raise HTTPException(status_code=404, detail="You don't belong to this organisation.")

    #now to switch
    current_user.active_org_id = org_id
    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return{"message": f"Switched to org {org_id}"}

@router.post("/add")
def add_user(org_id: int, add_data: InviteUserRequest, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    #check if the user is in the org already
    stmt = select(UserOrganisation).where((UserOrganisation.user_id == current_user.id) & (UserOrganisation.organisation_id == org_id)) & (User.active_org_id == org_id)
    member = session.exec(stmt).first()
    if not member:
        raise HTTPException(status_code=403, detail="You don't belong to this organisation.")

    #Find the user you want to invite
    stmt = select(User).where(User.email == add_data.email)
    wanted_user = session.exec(stmt).first()
    if not wanted_user:
        raise HTTPException(status_code=404, detail="User not found.")

    #check if they are in the org already
    stmt = select(UserOrganisation).where((UserOrganisation.user_id == wanted_user.id) & (UserOrganisation.organisation_id == org_id))
    existing_user = session.exec(stmt).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="User already in organisation.")

    #now link/add the user
    link = UserOrganisation(user_id=wanted_user.id, organisation_id=org_id)
    session.add(link)
    session.commit()

    return {"message", f"{wanted_user.email} added to the org{org_id}"}


@router.post("/invite")
def create_invite(org_id: int,
    invite_data: InviteUserRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Check if current user is in the org
    stmt = select(UserOrganisation).where(
        (UserOrganisation.user_id == current_user.id) &
        (UserOrganisation.organisation_id == org_id)
    )
    if not session.exec(stmt).first():
        raise HTTPException(status_code=403, detail="You're not in this organisation.")

    # check if current user is an owner or admin
    stmt = select(UserOrganisation).where(
        (UserOrganisation.user_id == current_user.id) &
        (UserOrganisation.organisation_id == org_id)
    )
    current_link = session.exec(stmt).first()
    if current_link.role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="You don't have permission to invite.")

    #Check if invite already exists and is pending
    stmt = select(Invite).where(
        (Invite.email == invite_data.email) &
        (Invite.organisation_id == org_id) &
        (Invite.accepted == False)
    )
    if session.exec(stmt).first():
        raise HTTPException(status_code=409, detail="Invite already sent")

    #Create the invite
    invite = Invite(
        email=invite_data.email,
        organisation_id=org_id,
        inviter_id=current_user.id
    )
    session.add(invite)
    session.commit()

    return {"message": f"Invite sent to {invite_data.email}"}


@router.post("/accept")
def accept_invite(
    org_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    #look for pending invite
    stmt = select(Invite).where(
        (Invite.email == current_user.email) &
        (Invite.organisation_id == org_id) &
        (Invite.accepted == False)
    )
    invite = session.exec(stmt).first()

    if not invite:
        raise HTTPException(status_code=404, detail="No valid invite found")

    #check if already a member
    stmt = select(UserOrganisation).where(
        (UserOrganisation.user_id == current_user.id) &
        (UserOrganisation.organisation_id == org_id)
    )
    if session.exec(stmt).first():
        raise HTTPException(status_code=409, detail="Already a member")

    #make a UserOrganisation link
    link = UserOrganisation(user_id=current_user.id, organisation_id=org_id)
    session.add(link)

    #mark invite as accepted
    invite.accepted = True
    session.add(invite)

    session.commit()
    return {"message": f"Joined organisation {org_id}"}


@router.patch("/promote")
def promote_user(
    org_id: int,
    data: PromoteUserRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    #check if current user is an owner
    stmt = select(UserOrganisation).where(
        (UserOrganisation.user_id == current_user.id) &
        (UserOrganisation.organisation_id == org_id)
    )
    current_link = session.exec(stmt).first()
    if current_link.role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    #find the user to promote
    target_user = session.exec(select(User).where(User.email == data.email)).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # get their org link
    stmt = select(UserOrganisation).where(
        (UserOrganisation.user_id == target_user.id) &
        (UserOrganisation.organisation_id == org_id)
    )
    link = session.exec(stmt).first()
    if not link:
        raise HTTPException(status_code=404, detail="User not in organization")

    # 4. Promote
    link.role = data.role
    session.add(link)
    session.commit()

    return {"message": f"{data.email} is now a {data.role}"}
