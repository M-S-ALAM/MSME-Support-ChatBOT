"""
This module provides utility functions for handling JWT tokens.
=====================================================================
Token utility functions for JWT creation and decoding.

- create_access_token(data: dict, expires_delta: timedelta):
    Creates a JWT access token with the given data and expiration.

- decode_access_token(token: str):
    Decodes and verifies a JWT access token. Returns the payload if valid, else None.

Environment:
- SECRET_KEY: Used for signing and verifying JWTs.
- ALGORITHM: JWT signing algorithm (default: HS256).
"""

import os
from jose import jwt, JWTError
from datetime import datetime, timedelta

SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=1)):
    """
    Create a JWT access token.

    Args:
        data (dict): The data to encode in the token.
        expires_delta (timedelta, optional): Token expiration time. Defaults to 1 hour.

    Returns:
        str: Encoded JWT token as a string.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    """
    Decode and verify a JWT access token.

    Args:
        token (str): The JWT token string.

    Returns:
        dict or None: Decoded payload if valid, else None.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
