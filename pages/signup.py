"""
This module contains the routes for the signup page of the FastAPI application.
============================================================================================
Signup page routes for FastAPI application.

Routes:
- GET /signup: Render the signup page.
- POST /signup: Register a new user and store in CSV.

Utilities:
- Uses bcrypt for password hashing.
"""

from fastapi import APIRouter, Request, status, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request as StarletteRequest
from email.message import EmailMessage
import os
import csv
import bcrypt
import smtplib
import random

router = APIRouter()
templates = Jinja2Templates(directory="templates")

SENDER_EMAIL = os.environ.get("MAIL_USERNAME")
SENDER_PASSWORD = os.environ.get("MAIL_PASSWORD")
verification_codes = {}

def send_otp_email(receiver_email, otp, sender_email, sender_password):
    msg = EmailMessage()
    msg['Subject'] = "Your OTP Code"
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg.set_content(f"Your OTP code is: {otp}")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        print(f"OTP sent to {receiver_email}")
    except Exception as e:
        print(f"Failed to send OTP: {e}")

@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """
    Render the signup page.
    """
    return templates.TemplateResponse("signup.html", {"request": request})

@router.post("/send_verification_code")
async def send_verification_code(data: dict):
    """
    Send a verification code to the user's email if username and email match.
    Uses fixed sender email and password from environment variables.
    """
    username = data.get("username")
    email = data.get("email")
    if not username or not email:
        return JSONResponse({"success": False, "message": "Username and email required."}, status_code=400)
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        return JSONResponse({
            "success": False,
            "message": "Sender email credentials not configured. Please set SENDER_EMAIL and SENDER_PASSWORD environment variables on the server."
        }, status_code=500)
    # For new user signup, just check if username already exists
    csv_path = os.path.join("Database", "users.csv")
    if not os.path.exists(csv_path):
        user_exists = False
    else:
        user_exists = False
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
            if rows:
                header_keywords = ['user', 'email', 'contact', 'auth']
                is_header = any(any(key in cell.lower() for key in header_keywords) for cell in rows[0])
                data_rows = rows[1:] if is_header else rows
                for row in data_rows:
                    if len(row) >= 1 and row[0].strip().lower() == username.strip().lower():
                        user_exists = True
                        break
    if user_exists:
        return JSONResponse({"success": False, "message": "Username already exists."}, status_code=400)
    otp = str(random.randint(100000, 999999))
    try:
        send_otp_email(email, otp, SENDER_EMAIL, SENDER_PASSWORD)
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Failed to send OTP: {e}"}, status_code=500)
    verification_codes[email] = otp
    return JSONResponse({"success": True, "message": "Verification code sent."})

@router.post("/verify_otp")
async def verify_otp(request: Request, data: dict):
    """
    Verify the OTP sent to the user's email.
    Expects: { "email": ..., "otp": ... }
    """
    email = data.get("email")
    otp = data.get("otp")
    if not email or not otp:
        return JSONResponse({"success": False, "message": "Email and OTP required."}, status_code=400)
    code = verification_codes.get(email)
    if code and code == otp:
        # Mark this email as verified in app state
        if not hasattr(request.app.state, "otp_store"):
            request.app.state.otp_store = {}
        request.app.state.otp_store[email] = True
        # Remove OTP from memory
        del verification_codes[email]
        return JSONResponse({"success": True, "message": "OTP verified successfully."})
    else:
        return JSONResponse({"success": False, "message": "Invalid or expired OTP."}, status_code=400)

@router.post("/signup")
async def signup_user(request: Request):
    """
    Register a new user, check for duplicates, and store in CSV.
    Requires OTP verification.
    """
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"success": False, "message": "Invalid JSON data."}, status_code=status.HTTP_400_BAD_REQUEST)
    username = data.get("username")
    email = data.get("email") or data.get("email_id")
    contact_number = data.get("contact_number")
    password = data.get("password") or data.get("signup_password")

    if not username or not email or not contact_number or not password:
        return JSONResponse({"success": False, "message": "All fields are required."}, status_code=status.HTTP_400_BAD_REQUEST)

    # Check OTP verification status
    otp_store = getattr(request.app.state, "otp_store", {})
    if not otp_store or not otp_store.get(email):
        return JSONResponse({"success": False, "message": "OTP not verified. Please verify OTP before signing up."}, status_code=status.HTTP_400_BAD_REQUEST)
    # Remove OTP verification status after successful signup
    del otp_store[email]
    request.app.state.otp_store = otp_store

    csv_path = os.path.join("Database", "users.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    # Check for duplicate username or email (allow duplicate passwords)
    if os.path.exists(csv_path):
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            try:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("username") == username:
                        return JSONResponse({"success": False, "message": "Username already exists."}, status_code=status.HTTP_400_BAD_REQUEST)
                    if row.get("email") == email:
                        return JSONResponse({"success": False, "message": "Email already exists."}, status_code=status.HTTP_400_BAD_REQUEST)
                # No password check here
            except Exception:
                pass  # If file is empty or malformed, allow signup to proceed
    # Hash the password before saving
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    # Write new user
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["username", "email", "contact_number", "password", "Authentication", "token_used"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists or os.stat(csv_path).st_size == 0:
            writer.writeheader()
        writer.writerow({
            "username": username,
            "email": email,
            "contact_number": contact_number,
            "password": hashed_password,
            "Authentication": "Pending",
            "token_used": "0"
        })
    # On success, return redirect URL to login page
    return JSONResponse({
        "success": True,
        "message": "Signup successful. Redirecting to login...",
        "redirect_url": "/"
    })