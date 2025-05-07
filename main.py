"""
This is the main FastAPI application file.
============================================================================================
Main FastAPI application entry point.

Includes routers for:
- admin
- admin_dashboard
- chat
- signup
- login
- forgot_password
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from pages.admin import router as admin_router
from pages.admin_dashboard import router as admin_dashboard_router
from pages.chat import router as chat_router
from pages.signup import router as signup_router
from pages.login import router as login_router
from pages.forgot_password import router as forgot_password_router

app = FastAPI()

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    print(f"WARNING: Static directory {static_dir} does not exist. Static files will not be served.")

app.include_router(admin_router)
app.include_router(admin_dashboard_router)
app.include_router(chat_router)
app.include_router(signup_router)
app.include_router(login_router)
app.include_router(forgot_password_router)