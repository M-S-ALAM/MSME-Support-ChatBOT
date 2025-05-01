from fastapi import FastAPI, Request, Form, status, Body
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import csv
import os
import bcrypt
from inference import LLMChatBot
from jwtsign import sign_token, get_current_user


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

chatbot = LLMChatBot()

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
    csv_path = os.path.join("Database", "users.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    # Check for duplicate username or email
    if os.path.exists(csv_path):
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["username"] == username or row["email"] == email:
                    return JSONResponse({"success": False, "message": "Username or email already exists."}, status_code=status.HTTP_400_BAD_REQUEST)
    # Hash the password before saving
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    # Write new user
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["username", "email", "password"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({"username": username, "email": email, "password": hashed_password})
    return JSONResponse({"success": True, "message": "Signup successful."})

@app.post("/login")
async def login_user(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return JSONResponse({"success": False, "message": "All fields are required."}, status_code=status.HTTP_400_BAD_REQUEST)
    csv_path = os.path.join("Database", "users.csv")
    if not os.path.exists(csv_path):
        return JSONResponse({"success": False, "message": "User database not found."}, status_code=status.HTTP_404_NOT_FOUND)
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Compare username after stripping and lowercasing for robustness
            if row["username"].strip().lower() == username.strip().lower():
                # Verify password using bcrypt (encrypted check)
                if bcrypt.checkpw(password.strip().encode("utf-8"), row["password"].encode("utf-8")):
                    # Generate JWT token using jwtsign
                    token = sign_token(row["email"])
                    print("Generated token:", token)
                    return JSONResponse({
                        "success": True,
                        "message": "Login successful.",
                        "access_token": token,
                        "token_type": "bearer"
                    })
    return JSONResponse({"success": False, "message": "Invalid username or password."}, status_code=status.HTTP_401_UNAUTHORIZED)

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.post("/get")
async def get_bot_response(data: dict = Body(...)):
    user_msg = data.get("msg", "")
    # Use your inference logic to get the bot reply
    _, result = chatbot.run(user_msg)
    if isinstance(result, dict) and "message" in result:
        return {"reply": result["message"]}
    elif isinstance(result, dict) and "error" in result:
        return {"reply": result["error"]}
    elif hasattr(result, "to_string"):
        return {"reply": result.to_string()}
    else:
        return {"reply": str(result)}

@app.get("/logout")
async def logout():
    # Optionally clear session/cookies here if implemented
    return RedirectResponse(url="/", status_code=302)

@app.get("/forgot_password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@app.post("/forgot_password")
async def forgot_password(
    username: str = Form(...),
    email: str = Form(...),
    new_password: str = Form(...),
):
    csv_path = os.path.join("Database", "users.csv")
    if not os.path.exists(csv_path):
        return JSONResponse({"success": False, "message": "User database not found."}, status_code=status.HTTP_404_NOT_FOUND)
    users = []
    user_found = False
    # Read all users and update the matching one
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["username"].strip().lower() == username.strip().lower() and row["email"].strip().lower() == email.strip().lower():
                # Update password
                row["password"] = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                user_found = True
            users.append(row)
    if not user_found:
        return JSONResponse({"success": False, "message": "Username and email do not match."}, status_code=status.HTTP_400_BAD_REQUEST)
    # Write back updated users
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["username", "email", "password"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(users)
    return JSONResponse({"success": True, "message": "Password reset successful."})