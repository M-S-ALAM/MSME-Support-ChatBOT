import os
from dotenv import load_dotenv
load_dotenv()  # <-- Make sure this is before any os.getenv calls

from fastapi import FastAPI, Request, HTTPException, Body
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel, EmailStr
from itsdangerous import URLSafeTimedSerializer
from typing import List

app = FastAPI()

# Configuration for sending emails
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS", "True") == "True",
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS", "False") == "True",
    USE_CREDENTIALS=True
)

# Model for email input
class EmailSchema(BaseModel):
    email: List[EmailStr]

# Secret key for token generation
SECRET_KEY = "your_secret_key" # Change to a secure, random value

# Function to generate verification token
def generate_token(email):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    return serializer.dumps(email, salt='email-verification')

# Function to verify token
def verify_token(token):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        email = serializer.loads(token, salt='email-verification', max_age=3600) # Token valid for 1 hour
        return email
    except Exception as e:
        return None

# Endpoint to request email verification
@app.post("/email/verification")
async def send_verification_email(email_data: EmailSchema = Body(...), request: Request = None):
    email = email_data.email[0]
    token = generate_token(email)
    verification_link = f"{request.base_url}verify-email?token={token}"

    message = MessageSchema(
        subject="Email Verification",
        recipients=email_data.email,
        body=f"""
        Please click the link below to verify your email:<br>
        <a href="{verification_link}">{verification_link}</a>
        """,
        subtype="html"
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        return {"message": "Verification email sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")

# Endpoint to verify email
@app.get("/verify-email")
async def verify_email(token: str):
    email = verify_token(token)
    if email:
        return {"message": f"Email {email} verified successfully!"}
    else:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
