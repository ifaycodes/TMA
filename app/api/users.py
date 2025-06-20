from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import  Session, select
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin
from app.db.session import get_session
from app.utils.security import hash_password, verify_password
from app.utils.token import create_access_token
from datetime import timedelta
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register")
def register_user(user: UserCreate, session: Session = Depends(get_session)):
    existing_user = session.exec(select(User).where(User.email == user.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        name=user.name,
        email=user.email,
        password=hash_password(user.password))

    #create new user
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return {"message": "User registered successfully", "user_id": new_user.id}

@router.get("/users")
def get_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return users

@router.post("/auth/login")
def login_user(user: UserLogin, session: Session = Depends(get_session)):
    #look up the user using email
    db_user = session.exec(select(User).where(User.email == user.email)).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")


    access_token = create_access_token(
        data = {"sub": str(db_user.id)},
        expires_delta = timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
    }