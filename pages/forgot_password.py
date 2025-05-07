"""
Forgot password routes for FastAPI application.

Routes:
- GET /forgot_password: Render the forgot password page.
- POST /send_verification_code: Send a verification code to the user's email.
- POST /forgot-password: Reset the user's password after verification.
- POST /verify_otp: Verify the OTP sent to the user's email.

Utilities:
- verification_codes: In-memory store for verification codes (for demo only).
"""

from fastapi import APIRouter, Request, Form, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import os
import csv
import bcrypt
import smtplib
import random
from email.message import EmailMessage
from dotenv import load_dotenv

router = APIRouter()
templates = Jinja2Templates(directory="templates")

verification_codes = {}

load_dotenv()  # Load environment variables from .env

SENDER_EMAIL = os.getenv("MAIL_USERNAME")
SENDER_PASSWORD = os.getenv("MAIL_PASSWORD")

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

@router.get("/forgot_password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """
    Render the forgot password page.
    """
    return templates.TemplateResponse("forgot_password.html", {"request": request})

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
        return JSONResponse({"success": False, "message": "Sender email credentials not configured."}, status_code=500)
    csv_path = os.path.join("Database", "users.csv")
    if not os.path.exists(csv_path):
        return JSONResponse({"success": False, "message": "User database not found."}, status_code=404)
    user_exists = False
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
        if not rows:
            return JSONResponse({"success": False, "message": "User database is empty."}, status_code=404)
        header_keywords = ['user', 'email', 'contact', 'auth']
        is_header = any(any(key in cell.lower() for key in header_keywords) for cell in rows[0])
        data_rows = rows[1:] if is_header else rows
        for row in data_rows:
            if len(row) >= 2:
                if row[0].strip().lower() == username.strip().lower() and row[1].strip().lower() == email.strip().lower():
                    user_exists = True
                    break
    if not user_exists:
        return JSONResponse({"success": False, "message": "Username and email do not match."}, status_code=400)
    otp = str(random.randint(100000, 999999))
    try:
        send_otp_email(email, otp, SENDER_EMAIL, SENDER_PASSWORD)
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Failed to send OTP: {e}"}, status_code=500)
    verification_codes[email] = otp
    return JSONResponse({"success": True, "message": "Verification code sent."})

@router.post("/verify_otp")
async def verify_otp(data: dict):
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
        return JSONResponse({"success": True, "message": "OTP verified successfully."})
    else:
        return JSONResponse({"success": False, "message": "Invalid or expired OTP."}, status_code=400)

@router.post("/forgot-password")
async def forgot_password(
    username: str = Form(...),
    email: str = Form(...),
    verification_code: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
):
    """
    Reset the user's password after verifying the code.
    """
    if new_password != confirm_password:
        return JSONResponse({"success": False, "message": "Passwords do not match."}, status_code=400)
    csv_path = os.path.join("Database", "users.csv")
    if not os.path.exists(csv_path):
        return JSONResponse({"success": False, "message": "User database not found."}, status_code=404)
    code = verification_codes.get(email)
    if not code or code != verification_code:
        return JSONResponse({"success": False, "message": "Invalid or expired verification code."}, status_code=400)
    users = []
    user_found = False
    fieldnames = []
    try:
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = [fn for fn in reader.fieldnames if fn is not None] if reader.fieldnames else []
            if not fieldnames:
                return JSONResponse({"success": False, "message": "User database is malformed."}, status_code=500)
            for row in reader:
                # Remove any None keys from the row to avoid DictWriter errors
                clean_row = {k: v for k, v in row.items() if k in fieldnames}
                if clean_row.get("username", "").strip().lower() == username.strip().lower() and clean_row.get("email", "").strip().lower() == email.strip().lower():
                    clean_row["password"] = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                    user_found = True
                users.append(clean_row)
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Error reading user database: {e}"}, status_code=500)
    if not user_found:
        return JSONResponse({"success": False, "message": "Username and email do not match."}, status_code=400)
    if not users:
        return JSONResponse({"success": False, "message": "No users found in database."}, status_code=500)
    try:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in users:
                # Only write fields that are in fieldnames
                writer.writerow({k: row.get(k, "") for k in fieldnames})
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Error writing user database: {e}"}, status_code=500)
    verification_codes.pop(email, None)
    return JSONResponse({"success": True, "message": "Password reset successful. Redirecting to login...", "redirect_url": "/"})
