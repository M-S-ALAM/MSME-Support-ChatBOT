"""
This module defines the routes and utilities for the admin section of the application.
=============================================================================================
Admin page routes for FastAPI application.

Routes:
- GET /admin: Render the admin login page.
- GET /admin_dashboard: Render the admin dashboard (requires admin session).
- GET /admin_users: Return a list of users for admin (requires admin session).
- POST /admin_login: Handle admin login.
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
    Return a list of users for admin (requires admin session).
    """
    if not is_admin_logged_in(request):
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=401)
    users = []
    csv_path = os.path.join("Database", "users.csv")
    if os.path.exists(csv_path):
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                users.append(row)
    return JSONResponse({"success": True, "users": users})

@router.post("/admin_login")
async def admin_login(request: Request):
    """
    Handle admin login.
    """
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    ADMIN_USERNAME = "gyandata"
    ADMIN_PASSWORD = "gyandata"  # Change this to your desired admin password

    if not username or not password:
        return JSONResponse({"success": False, "message": "All fields are required."}, status_code=400)
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        response = JSONResponse({"success": True, "message": "Admin login successful.", "redirect_url": "/admin_dashboard"})
        response.set_cookie(key="admin_logged_in", value="true", httponly=True)
        return response
    else:
        return JSONResponse({"success": False, "message": "Invalid admin credentials."}, status_code=401)

@router.get("/admin_logout")
async def admin_logout():
    """
    Logout the admin and clear the session cookie.
    """
    response = RedirectResponse(url="/admin", status_code=302)
    response.delete_cookie("admin_logged_in")
    return response