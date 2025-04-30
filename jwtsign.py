# jwtsign.py

import time
import jwt
import secrets
from fastapi import HTTPException, Request

JWT_SECRET = secrets.token_hex(16)
JWT_ALGORITHM = "HS256"

def sign_token(email: str) -> str:
    payload = {
        "email": email,
        "exp": time.time() + 3600  # expires in 1 hour
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def decode_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = auth_header.split(" ")[1]
    return decode_token(token)

def test_jwt():
    # Test the JWT signing and decoding
    test_email = "shahbazlam@gyandata.com"
    token = sign_token(test_email)
    print("Generated token:", token)
    # Test decoding
    try:
        decoded_payload = decode_token(token)
        print("Decoded payload:", decoded_payload)
    except Exception as e:
        print("Error decoding token:", e)

if __name__ == "__main__":
    test_jwt()
