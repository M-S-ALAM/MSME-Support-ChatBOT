"""
This module defines the routes and utilities for the admin section of the application.
=============================================================================================
Admin page routes for FastAPI application.

Routes:
- GET /admin: Render the admin login page.
- GET /admin_dashboard: Render the admin dashboard (requires admin session).
- GET /admin_users: Return a list of users for admin (requires admin session).
- GET /admin_logout: Logout admin and clear session cookie.

Utilities:
- is_admin_logged_in(request): Checks if admin session cookie is set.
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os
import csv

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def is_admin_logged_in(request: Request):
    """
    Check if the admin is logged in by verifying the session cookie.
    """
    return request.cookies.get("admin_logged_in") == "true"

@router.get("/admin", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """
    Render the admin login page.
    """
    return templates.TemplateResponse("admin.html", {"request": request})

@router.get("/admin_dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """
    Render the admin dashboard page if admin is logged in.
    """
    if not is_admin_logged_in(request):
        return RedirectResponse(url="/admin", status_code=302)
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

@router.get("/admin_users")
async def admin_users(request: Request):
    """
    Return a list of users for the admin dashboard.
    """
    if not is_admin_logged_in(request):
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=401)
    csv_path = os.path.join("Database", "users.csv")
    users = []
    if os.path.exists(csv_path):
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
            if not rows:
                return JSONResponse({"success": True, "users": []})
            header_keywords = ['user', 'email', 'contact', 'auth']
            is_header = any(any(key in str(cell).lower() for key in header_keywords) for cell in rows[0])
            data_rows = rows[1:] if is_header else rows
            for row in data_rows:
                if not any(row):
                    continue
                user = {}
                if len(row) >= 1:
                    user["username"] = row[0]
                if len(row) >= 2:
                    user["email"] = row[1]
                if len(row) >= 3:
                    user["contact_number"] = row[2]
                user["Authentication"] = row[4] if len(row) > 4 else "no"
                user["token_used"] = row[5] if len(row) > 5 else "0"
                users.append(user)
    return JSONResponse({"success": True, "users": users})

@router.get("/admin_logout")
async def admin_logout():
    """
    Logout the admin and clear the session cookie.
    """
    response = RedirectResponse(url="/admin", status_code=302)
    response.delete_cookie("admin_logged_in")
    return response