from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import os
import csv
import bcrypt
from jwtsign import sign_token

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login_user(request: Request):
    try:
        data = await request.json()
        username = data.get("username", "").strip()
        password = data.get("password", "")

        if not username or not password:
            return JSONResponse({"success": False, "message": "All fields are required."}, status_code=status.HTTP_400_BAD_REQUEST)

        csv_path = os.path.join("Database", "users.csv")
        if not os.path.exists(csv_path):
            return JSONResponse({"success": False, "message": "User database not found."}, status_code=status.HTTP_404_NOT_FOUND)

        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            try:
                reader = csv.DictReader(f)
                for row in reader:
                    vals = list(row.values())
                    row_username = (row.get("username") or row.get("Username") or (vals[0] if len(vals) > 0 else "")).strip().lower()
                    row_password_hash = row.get("password") or row.get("Password") or (vals[3] if len(vals) > 3 else "")
                    row_email = row.get("email") or row.get("Email") or (vals[1] if len(vals) > 1 else "")
                    if not row_username or not row_password_hash:
                        continue
                    try:
                        if row_username == username.lower() and row_password_hash:
                            if bcrypt.checkpw(password.encode("utf-8"), row_password_hash.encode("utf-8")):
                                token = sign_token(row_email)
                                response = JSONResponse({
                                    "success": True,
                                    "message": "Login successful.",
                                    "access_token": token,
                                    "token_type": "bearer",
                                    "redirect_url": "/chat"
                                })
                                response.set_cookie(
                                    key="access_token",
                                    value=token,
                                    httponly=True,
                                    path="/",
                                    samesite="lax"
                                )
                                return response
                    except Exception:
                        continue
            except Exception:
                return JSONResponse({"success": False, "message": "Server error reading user database."}, status_code=500)

        return JSONResponse({"success": False, "message": "Invalid username or password."}, status_code=status.HTTP_401_UNAUTHORIZED)

    except Exception:
        return JSONResponse({"success": False, "message": "An error occurred during login."}, status_code=500)
