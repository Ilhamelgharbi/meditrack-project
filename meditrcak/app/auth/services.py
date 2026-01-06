from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from app.auth.models import User, RoleEnum
from app.auth.schemas import UserRegister, TokenData
from app.auth.utils import hash_password, verify_password, decode_access_token
from app.database.db import get_db
from typing import Optional

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def create_user(db: Session, user_data: UserRegister) -> User:
    """Create a new user in the database"""
    from app.patients.services import PatientService
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    new_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        phone=user_data.phone,
        password_hash=hash_password(user_data.password),
        role=user_data.role
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # If user is a patient, create patient profile automatically
    if new_user.role == RoleEnum.patient:
        PatientService.create_patient_profile(db, new_user.id)

    return new_user

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password"""
    print(f"DEBUG: authenticate_user called with email: {email}")

    user = db.query(User).filter(User.email == email).first()
    print(f"DEBUG: User query result: {user}")

    if not user:
        print("DEBUG: User not found")
        return None

    print(f"DEBUG: Verifying password for user: {user.email}")
    password_valid = verify_password(password, user.password_hash)
    print(f"DEBUG: Password verification result: {password_valid}")

    if not password_valid:
        print("DEBUG: Password verification failed")
        return None

    print("DEBUG: Authentication successful")
    return user

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email"""
    return db.query(User).filter(User.email == email).first()

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = decode_access_token(token)

    if token_data is None or token_data.email is None:
        raise credentials_exception

    user = get_user_by_email(db, email=token_data.email)

    if user is None:
        raise credentials_exception

    return user

def require_role(required_roles: list[RoleEnum]):
    """Dependency to check if user has required role"""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[role.value for role in required_roles]}"
            )
        return current_user
    return role_checker
require_admin = require_role([RoleEnum.admin])
require_patient = require_role([RoleEnum.patient])
