from fastapi import APIRouter, Request, Form, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import os
import csv
import bcrypt

router = APIRouter()
templates = Jinja2Templates(directory="templates")

verification_codes = {}

@router.get("/forgot_password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@router.post("/send_verification_code")
async def send_verification_code(data: dict):
    username = data.get("username")
    email = data.get("email")
    if not username or not email:
        return JSONResponse({"success": False, "message": "Username and email required."}, status_code=400)
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
            if len(row) >= 1 and len(row) >= 2:
                if row[0].strip().lower() == username.strip().lower() and row[1].strip().lower() == email.strip().lower():
                    user_exists = True
                    break
    if not user_exists:
        return JSONResponse({"success": False, "message": "Username and email do not match."}, status_code=400)
    import random
    code = str(random.randint(100000, 999999))
    verification_codes[email] = code
    # Here you would send the code via email (omitted for brevity)
    return JSONResponse({"success": True, "message": "Verification code sent."})

@router.post("/forgot-password")
async def forgot_password(
    username: str = Form(...),
    email: str = Form(...),
    verification_code: str = Form(...),
    new_password: str = Form(...),
):
    csv_path = os.path.join("Database", "users.csv")
    if not os.path.exists(csv_path):
        return JSONResponse({"success": False, "message": "User database not found."}, status_code=404)
    code = verification_codes.get(email)
    if not code or code != verification_code:
        return JSONResponse({"success": False, "message": "Invalid or expired verification code."}, status_code=400)
    users = []
    user_found = False
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["username"].strip().lower() == username.strip().lower() and row["email"].strip().lower() == email.strip().lower():
                row["password"] = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                user_found = True
            users.append(row)
    if not user_found:
        return JSONResponse({"success": False, "message": "Username and email do not match."}, status_code=400)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["username", "email", "contact_number", "password"] if "contact_number" in users[0] else ["username", "email", "password"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(users)
    verification_codes.pop(email, None)
    return JSONResponse({"success": True, "message": "Password reset successful."})
