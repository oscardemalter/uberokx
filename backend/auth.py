from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from backend.config import settings
import time
from collections import defaultdict
from functools import wraps
from flask import request, redirect

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
login_attempts = defaultdict(list)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=12))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def check_rate_limit(ip: str) -> bool:
    now = time.time()
    login_attempts[ip] = [t for t in login_attempts[ip] if now - t < 300]
    return len(login_attempts[ip]) < 5


def record_attempt(ip: str):
    login_attempts[ip].append(time.time())


def require_auth(f):
    """Décorateur pour protéger les routes Flask"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request, redirect, url_for
        token = request.cookies.get("access_token")
        if not token:
            return redirect(url_for('login'))
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            if payload.get("sub") != settings.ADMIN_EMAIL:
                return redirect(url_for('login'))
        except JWTError:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
