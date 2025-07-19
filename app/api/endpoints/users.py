from typing import List
from fastapi import APIRouter, Depends, HTTPException , status
from sqlalchemy.orm import Session
from app.core.security import get_current_admin_user, get_current_user
from app.database import get_db
from app.models import user as user_model
from app.schemas import user as user_schema
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create a new router for user-related endpoints
router = APIRouter(
    prefix="/users",  # URL prefix for all routes in this router
    tags=["Users"]  # Tags for documentation purposes
)

@router.post("/", response_model=user_schema.UserOut, status_code=status.HTTP_201_CREATED)
def create_user(request: user_schema.UserCreate, db: Session = Depends(get_db)):
    # Optional: check if user already exists
    existing_user = db.query(user_model.User).filter(user_model.User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash the password before storing it
    hashed_password = pwd_context.hash(request.password)

    # Create a new user instance and add it to the database

    new_user = user_model.User(
        email=request.email,
        password=hashed_password ,
        role=request.role # You should hash this before storing!
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/", response_model=List[user_schema.ShowUser])
def get_all_users(db: Session = Depends(get_db), current_user: user_schema.UserBase = Depends(get_current_user)):
    users = db.query(user_model.User).all()
    return users

@router.get('/{id}', response_model=user_schema.ShowUser, status_code=status.HTTP_200_OK,dependencies=[Depends(get_current_admin_user)])
def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(user_model.User).filter(user_model.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'User with id {id} not found')
    return user

@router.post('/{id}', response_model=user_schema.ShowUser, status_code=status.HTTP_200_OK)
def update_user(id: int, request: user_schema.UserUpdate, db: Session = Depends(get_db), current_user: user_schema.UserBase = Depends(get_current_user)):
    user = db.query(user_model.User).filter(user_model.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'User with id {id} not found')
    
    # Update the user's details
    if request.email:
        user.email = request.email
    if request.is_active is not None:
        user.is_active = request.is_active
    
    db.commit()
    db.refresh(user)
    return user

@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_user(id: int, db: Session = Depends(get_db), current_user: user_schema.UserBase = Depends(get_current_user)):
    user = db.query(user_model.User).filter(user_model.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'User with id {id} not found')
    
    db.delete(user)
    db.commit()
    return {"detail": "User deleted successfully"}