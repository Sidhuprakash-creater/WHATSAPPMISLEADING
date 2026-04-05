"""
Authentication — JWT login/refresh (simplified for hackathon)
"""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from jose import jwt, JWTError
from config import get_settings

router = APIRouter()
settings = get_settings()


class LoginRequest(BaseModel):
    email: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    """Simple email-based login (no password for hackathon demo)"""
    access_token = create_token(
        {"sub": body.email}, 
        timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    refresh_token = create_token(
        {"sub": body.email, "type": "refresh"}, 
        timedelta(days=7)
    )
    return TokenResponse(
        access_token=access_token, 
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """Refresh expired access token"""
    try:
        payload = jwt.decode(
            refresh_token, settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        email = payload.get("sub")
        if not email:
            raise HTTPException(401, "Invalid token")
    except JWTError:
        raise HTTPException(401, "Invalid or expired refresh token")
    
    new_access = create_token(
        {"sub": email}, 
        timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    new_refresh = create_token(
        {"sub": email, "type": "refresh"}, 
        timedelta(days=7)
    )
    return TokenResponse(
        access_token=new_access, 
        refresh_token=new_refresh
    )
