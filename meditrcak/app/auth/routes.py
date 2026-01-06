from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.auth.schemas import UserRegister, UserResponse, Token
from app.auth.services import create_user, authenticate_user, get_current_user
from app.auth.utils import create_access_token
from app.auth.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user

    - **full_name**: User's full name
    - **email**: User's email (must be unique)
    - **phone**: User's phone number (optional)
    - **password**: User's password (min 6 characters)
    - **role**: User's role (patient or admin, default: patient)
    """
    try:
        new_user = create_user(db, user_data)
        return new_user
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login to get access token

    - **username**: User's email
    - **password**: User's password
    """
    print(f"DEBUG: Login attempt for email: {form_data.username}")

    user = authenticate_user(db, form_data.username, form_data.password)
    print(f"DEBUG: authenticate_user returned: {user}")

    if not user:
        print("DEBUG: User authentication failed - returning 401")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    print(f"DEBUG: User authenticated successfully: {user.email}, role: {user.role}")

    # Create access token
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value}
    )

    print("DEBUG: Access token created successfully")

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information

    Requires valid JWT token in Authorization header
    """
    return current_user
