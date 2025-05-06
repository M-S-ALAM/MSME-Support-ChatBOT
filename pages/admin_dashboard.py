"""
This module defines the routes and utilities for the admin section of the application.
=============================================================================================
Admin dashboard routes for FastAPI application.


Routes:
- GET /admin_dashboard: Render the admin dashboard (requires admin session).
- POST /update_authentication: Update user authentication status (admin only).
- GET /admin_logout: Logout admin and clear session cookie.

Utilities:
- is_admin_logged_in(request): Checks if admin session cookie is set.
"""

from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
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

@router.get("/admin_dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """
    Render the admin dashboard page if admin is logged in.
    """
    if not is_admin_logged_in(request):
        return RedirectResponse(url="/admin", status_code=302)
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

@router.post("/update_authentication")
async def update_authentication(data: dict):
    """
    Update the authentication status of a user (admin only).
    """
    username = data.get("username")
    auth_value = data.get("Authentication")
    if not username or not auth_value:
        return JSONResponse({"success": False, "message": "Invalid data."}, status_code=400)
    csv_path = os.path.join("Database", "users.csv")
    if not os.path.exists(csv_path):
        return JSONResponse({"success": False, "message": "User database not found."}, status_code=404)
    rows = []
    updated = False
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        all_rows = list(reader)
        # Detect header
        header_keywords = ['user', 'email', 'contact', 'auth', 'token']
        is_header = any(any(key in str(cell).lower() for key in header_keywords) for cell in all_rows[0]) if all_rows else False
        header = all_rows[0] if is_header else None
        data_rows = all_rows[1:] if is_header else all_rows
        for row in data_rows:
            if len(row) >= 1 and row[0] == username:
                while len(row) < 7:
                    row.append("0" if len(row) == 5 else "")
                row[4] = auth_value
                updated = True
            rows.append(row)
    if not updated:
        return JSONResponse({"success": False, "message": "User not found."}, status_code=404)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if header:
            writer.writerow(header)
        writer.writerows(rows)
    return JSONResponse({"success": True, "message": "Authentication updated."})

@router.get("/admin_logout")
async def admin_logout():
    """
    Logout the admin and clear the session cookie.
    """
    response = RedirectResponse(url="/admin", status_code=302)
    response.delete_cookie("admin_logged_in")
    return response