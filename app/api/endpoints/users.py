from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
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

@router.post("/create_user", response_model=user_schema.UserBase)
def create_user(request: user_schema.UserBase, db: Session = Depends(get_db)):
    # Optional: check if user already exists
    existing_user = db.query(user_model.User).filter(user_model.User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash the password before storing it
    request.password = pwd_context.hash(request.password)

    # Create a new user instance and add it to the database

    new_user = user_model.User(
        username=request.username,
        email=request.email,
        password=request.password  # You should hash this before storing!
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user