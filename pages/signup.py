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

from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import os
import csv
import bcrypt

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """
    Render the signup page.
    """
    return templates.TemplateResponse("signup.html", {"request": request})

@router.post("/signup")
async def signup_user(request: Request):
    """
    Register a new user, check for duplicates, and store in CSV.
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
    csv_path = os.path.join("Database", "users.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    # Check for duplicate username, email, or contact number
    if os.path.exists(csv_path):
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            try:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("username") == username or row.get("email") == email or row.get("contact_number") == contact_number:
                        return JSONResponse({"success": False, "message": "Username, email, or contact number already exists."}, status_code=status.HTTP_400_BAD_REQUEST)
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
    return JSONResponse({"success": True, "message": "Signup successful."})