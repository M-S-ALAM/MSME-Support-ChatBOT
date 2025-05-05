from fastapi import FastAPI, Request, Form, status, Body, BackgroundTasks, Depends, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import HTTPConnection
import csv
import os
import bcrypt
import random
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from inference import LLMChatBot
from jwtsign import sign_token, get_current_user
from jose import JWTError
from jose import jwt
from dotenv import load_dotenv

SECRET_KEY = "your-secret-key"  # Use your actual secret key
ALGORITHM = "HS256"

def get_current_user_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

# Helper to check admin session (very basic, for demonstration)
def is_admin_logged_in(request: Request):
    return request.cookies.get("admin_logged_in") == "true"

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

verification_codes = {}  # In-memory store for demo; use a persistent store in production

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
    email = data.get("email") or data.get("email_id")  # Accept both keys for compatibility
    contact_number = data.get("contact_number")
    password = data.get("password") or data.get("signup_password")  # Accept both keys for compatibility
    if not username or not email or not contact_number or not password:
        return JSONResponse({"success": False, "message": "All fields are required."}, status_code=status.HTTP_400_BAD_REQUEST)
    csv_path = os.path.join("Database", "users.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    # Check for duplicate username, email, or contact number
    if os.path.exists(csv_path):
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["username"] == username or row["email"] == email or row.get("contact_number") == contact_number:
                    return JSONResponse({"success": False, "message": "Username, email, or contact number already exists."}, status_code=status.HTTP_400_BAD_REQUEST)
    # Hash the password before saving
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    # Write new user
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["username", "email", "contact_number", "password"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({"username": username, "email": email, "contact_number": contact_number, "password": hashed_password})
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
                # Defensive: check for missing password field
                row_password = row.get("password")
                if not row_password:
                    continue
                # Defensive: handle possible whitespace in password field
                if bcrypt.checkpw(password.strip().encode("utf-8"), row_password.strip().encode("utf-8")):
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
    user = get_current_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/", status_code=302)
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

@app.post("/send_verification_code")
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
        reader = csv.DictReader(f)
        for row in reader:
            if row["username"].strip().lower() == username.strip().lower() and row["email"].strip().lower() == email.strip().lower():
                user_exists = True
                break
    if not user_exists:
        return JSONResponse({"success": False, "message": "Username and email do not match."}, status_code=400)
    # Generate code and send email
    code = str(random.randint(100000, 999999))
    verification_codes[email] = code
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        message = Mail(
            from_email='from_email@example.com',
            to_emails=email,
            subject='Your Password Reset Verification Code',
            html_content=f'<strong>Your verification code is: {code}</strong>')
        sg.send(message)
    except Exception as e:
        return JSONResponse({"success": False, "message": "Failed to send email."}, status_code=500)
    return JSONResponse({"success": True, "message": "Verification code sent."})

@app.post("/forgot-password")
async def forgot_password(
    username: str = Form(...),
    email: str = Form(...),
    verification_code: str = Form(...),
    new_password: str = Form(...),
):
    csv_path = os.path.join("Database", "users.csv")
    if not os.path.exists(csv_path):
        return JSONResponse({"success": False, "message": "User database not found."}, status_code=404)
    # Verify code
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
        # Add contact_number to fieldnames if not present
        fieldnames = ["username", "email", "contact_number", "password"] if "contact_number" in users[0] else ["username", "email", "password"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(users)
    # Remove code after use
    verification_codes.pop(email, None)
    return JSONResponse({"success": True, "message": "Password reset successful."})

@app.get("/admin", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    # Optionally, check for admin session/cookie here
    return templates.TemplateResponse("admin.html", {"request": request})

@app.post("/admin_login")
async def admin_login(request: Request):
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

@app.get("/admin_dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    if not is_admin_logged_in(request):
        return RedirectResponse(url="/admin", status_code=302)
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

@app.get("/admin_users")
async def admin_users(request: Request):
    if not is_admin_logged_in(request):
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=401)
    csv_path = os.path.join("Database", "users.csv")
    users = []
    # Try to support both lower-case and capitalized CSV headers for compatibility
    if os.path.exists(csv_path):
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                users.append({
                    "username": row.get("username", "") or row.get("Username", ""),
                    "email": row.get("email", "") or row.get("Email", ""),
                    "contact_number": row.get("contact_number", "") or row.get("Contact Number", ""),
                    "Authentication": row.get("Authentication", "no")
                })
    return JSONResponse({"success": True, "users": users})

@app.post("/update_authentication")
async def update_authentication(data: dict):
    username = data.get("username")
    auth_value = data.get("Authentication")
    if not username or not auth_value:
        return JSONResponse({"success": False, "message": "Invalid data."}, status_code=400)
    csv_path = os.path.join("Database", "users.csv")
    if not os.path.exists(csv_path):
        return JSONResponse({"success": False, "message": "User database not found."}, status_code=404)
    users = []
    updated = False
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        # Support both lower-case and capitalized username field
        if "Authentication" not in fieldnames:
            fieldnames = fieldnames + ["Authentication"]
        for row in reader:
            row_username = row.get("username", "") or row.get("Username", "")
            if row_username == username:
                row["Authentication"] = auth_value
                updated = True
            if "Authentication" not in row:
                row["Authentication"] = "no"
            users.append(row)
    if not updated:
        return JSONResponse({"success": False, "message": "User not found."}, status_code=404)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(users)
    return JSONResponse({"success": True, "message": "Authentication updated."})

@app.get("/admin_logout")
async def admin_logout():
    response = RedirectResponse(url="/admin", status_code=302)
    response.delete_cookie("admin_logged_in")
    return response