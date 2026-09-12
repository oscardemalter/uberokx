"""
Authentication and authorization module for UberOKX.
Handles JWT token creation, rate limiting, and user verification.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from backend.config import settings
import time
from collections import defaultdict


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
login_attempts = defaultdict(list)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with optional expiration.
    
    Args:
        data: Dictionary containing token claims (e.g., {"sub": email})
        expires_delta: Optional timedelta for token expiration
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=12))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def check_rate_limit(ip: str, max_attempts: int = 5, window_seconds: int = 300) -> bool:
    """
    Check if IP address has exceeded login attempt rate limit.
    
    Args:
        ip: Client IP address
        max_attempts: Maximum allowed attempts in time window
        window_seconds: Time window in seconds
        
    Returns:
        True if within limit, False if exceeded
    """
    now = time.time()
    # Clean old attempts outside the window
    login_attempts[ip] = [t for t in login_attempts[ip] if now - t < window_seconds]
    return len(login_attempts[ip]) < max_attempts


def record_attempt(ip: str) -> None:
    """
    Record a failed login attempt for rate limiting.
    
    Args:
        ip: Client IP address
    """
    login_attempts[ip].append(time.time())


async def get_current_user(request) -> dict:
    """
    Verify JWT token from request cookies and return user info.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Dictionary with user information
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token manquant"
        )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        if email is None or email != settings.ADMIN_EMAIL:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide"
            )
        return {"email": email}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré"
        )
