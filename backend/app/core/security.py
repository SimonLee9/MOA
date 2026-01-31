"""
Security utilities for authentication
JWT token generation, password hashing, and security utilities
"""

import re
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

logger = logging.getLogger(__name__)


# Password hashing context with secure defaults
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Secure work factor
)

# Password validation rules
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


class PasswordValidationError(Exception):
    """Raised when password does not meet requirements"""
    pass


def validate_password_strength(password: str) -> bool:
    """
    Validate password meets security requirements

    Requirements:
    - Minimum 8 characters
    - Maximum 128 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character (@$!%*?&)

    Raises:
        PasswordValidationError: If password doesn't meet requirements
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        raise PasswordValidationError(
            f"Password must be at least {PASSWORD_MIN_LENGTH} characters"
        )

    if len(password) > PASSWORD_MAX_LENGTH:
        raise PasswordValidationError(
            f"Password must be at most {PASSWORD_MAX_LENGTH} characters"
        )

    if not re.search(r"[a-z]", password):
        raise PasswordValidationError("Password must contain a lowercase letter")

    if not re.search(r"[A-Z]", password):
        raise PasswordValidationError("Password must contain an uppercase letter")

    if not re.search(r"\d", password):
        raise PasswordValidationError("Password must contain a digit")

    if not re.search(r"[@$!%*?&#^()_+=\-\[\]{}|\\:\";<>,./?]", password):
        raise PasswordValidationError(
            "Password must contain a special character"
        )

    return True


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password (truncated to 72 bytes for bcrypt)"""
    # bcrypt has a 72-byte password limit
    # Truncate UTF-8 encoded password to 72 bytes
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    truncated_password = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.hash(truncated_password)


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token"""
    return secrets.token_urlsafe(length)


def sanitize_user_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent injection attacks

    Args:
        text: Raw user input
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not text:
        return ""

    # Truncate to max length
    text = text[:max_length]

    # Remove null bytes
    text = text.replace("\x00", "")

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def create_access_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Payload data to encode
        expires_delta: Optional custom expiration time
    
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def create_refresh_token(data: dict[str, Any]) -> str:
    """
    Create a JWT refresh token with longer expiration
    
    Args:
        data: Payload data to encode
    
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def decode_token(token: str) -> Optional[dict[str, Any]]:
    """
    Decode and validate a JWT token
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None
