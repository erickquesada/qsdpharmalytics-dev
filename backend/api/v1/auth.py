from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from backend.database.base import get_db
from backend.schemas.user import UserLogin, Token, UserCreate, UserResponse
from backend.models.user import User
from backend.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    create_refresh_token,
    verify_token
)
from backend.core.config import settings

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    
    # Check if user already exists
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        hashed_password=hashed_password,
        role=user.role,
        phone=user.phone,
        department=user.department,
        manager_id=user.manager_id,
        is_active=True,
        is_verified=False  # Email verification can be added later
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token"""
    
    # Find user by username or email
    user = None
    if "@" in user_credentials.username_or_email:
        user = db.query(User).filter(User.email == user_credentials.username_or_email).first()
    else:
        user = db.query(User).filter(User.username == user_credentials.username_or_email).first()
    
    # Verify user and password
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    additional_claims = {
        "role": user.role.value,
        "username": user.username,
        "full_name": user.full_name
    }
    
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=access_token_expires,
        additional_claims=additional_claims
    )
    
    refresh_token = create_refresh_token(subject=str(user.id))
    
    # Update last login
    from sqlalchemy.sql import func
    user.last_login = func.now()
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    
    try:
        payload = verify_token(refresh_token, "refresh")
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        additional_claims = {
            "role": user.role.value,
            "username": user.username,
            "full_name": user.full_name
        }
        
        new_access_token = create_access_token(
            subject=str(user.id),
            expires_delta=access_token_expires,
            additional_claims=additional_claims
        )
        
        new_refresh_token = create_refresh_token(subject=str(user.id))
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout():
    """Logout user (client should discard tokens)"""
    return {"message": "Successfully logged out"}


# For testing purposes - create admin user
@router.post("/create-admin", response_model=UserResponse, include_in_schema=False)
async def create_admin_user(db: Session = Depends(get_db)):
    """Create admin user for testing (remove in production)"""
    
    # Check if admin already exists
    if db.query(User).filter(User.username == "admin").first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin user already exists"
        )
    
    from models.user import UserRole
    
    admin_user = User(
        email="admin@pharmalitics.com",
        username="admin",
        first_name="System",
        last_name="Administrator",
        hashed_password=get_password_hash("admin"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    return admin_user