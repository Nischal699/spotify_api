from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.security import Hash , create_access_token, get_current_user
from app import database  # assuming your get_db is here
from app.models import user as user_model
from app.schemas.auth import TokenData

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/login")
def login(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(user_model.User).filter(user_model.User.email == request.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not Hash.verify(request.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")
    
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    if not access_token:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create access token")
    return {"access_token": access_token, "token_type": "bearer", "role": user.role, "email": user.email}

@router.get("/validate_token")
def validate_token(current_user: TokenData = Depends(get_current_user)):
    return {"status": "valid", "email": current_user.email}