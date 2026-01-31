"""
Authentication Endpoints
User registration, login, and profile management
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from bson import ObjectId

from app.schemas.user import UserRegister, UserLogin, Token, UserResponse, User
from app.core.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user
)
from app.services.mongodb_service import get_db
from app.core.logging import logger
from app.core.time import now_ist, format_ist

router = APIRouter()


@router.post("/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """
    Register a new user
    """
    db = get_db()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable"
        )
    
    # Check if username already exists
    if db.users.find_one({"username": user_data.username}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    if db.users.find_one({"email": user_data.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user document
    created_at = now_ist()
    user_doc = {
        "username": user_data.username,
        "email": user_data.email,
        "password_hash": get_password_hash(user_data.password),
        "created_at": created_at,
        "created_at_str": format_ist(created_at, include_tz=True),
        "active": True,
        "settings": {
            "email_notifications": True,
            "slack_notifications": False
        }
    }
    
    result = db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    logger.info(f"[Auth] New user registered: {user_data.username} (ID: {user_id})")
    
    # Create access token
    access_token = create_access_token(
        data={"user_id": user_id, "username": user_data.username}
    )
    
    return Token(access_token=access_token)


@router.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Login with username and password
    """
    db = get_db()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable"
        )
    
    # Find user by username
    user_doc = db.users.find_one({"username": credentials.username})
    
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, user_doc["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Check if user is active
    if not user_doc.get("active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    user_id = str(user_doc["_id"])
    logger.info(f"[Auth] User logged in: {credentials.username} (ID: {user_id})")
    
    # Create access token
    access_token = create_access_token(
        data={"user_id": user_id, "username": credentials.username}
    )
    
    return Token(access_token=access_token)


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(user: User = Depends(get_current_user)):
    """
    Get current authenticated user information
    """
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        active=user.active
    )
