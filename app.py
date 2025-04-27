from fastapi import FastAPI, Request, Form, status, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import csv
import os

app = FastAPI()

# Enable CORS for all origins (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
async def signup_user(request: Request):
    data = await request.json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    if not username or not email or not password:
        return JSONResponse({"success": False, "message": "All fields are required."}, status_code=status.HTTP_400_BAD_REQUEST)
    csv_path = os.path.join("database", "users.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    # Check for duplicate username or email
    if os.path.exists(csv_path):
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["username"] == username or row["email"] == email:
                    return JSONResponse({"success": False, "message": "Username or email already exists."}, status_code=status.HTTP_400_BAD_REQUEST)
    # Write new user
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["username", "email", "password"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({"username": username, "email": email, "password": password})
    return JSONResponse({"success": True, "message": "Signup successful."})

@app.post("/login")
async def login_user(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return JSONResponse({"success": False, "message": "All fields are required."}, status_code=status.HTTP_400_BAD_REQUEST)
    csv_path = os.path.join("database", "users.csv")
    if not os.path.exists(csv_path):
        return JSONResponse({"success": False, "message": "User database not found."}, status_code=status.HTTP_404_NOT_FOUND)
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["username"] == username and row["password"] == password:
                return JSONResponse({"success": True, "message": "Login successful."})
    return JSONResponse({"success": False, "message": "Invalid username or password."}, status_code=status.HTTP_401_UNAUTHORIZED)

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.post("/get")
async def get_bot_response(data: dict = Body(...)):
    # Always reply with "hello" (as per your previous request)
    return {"reply": "hello"}