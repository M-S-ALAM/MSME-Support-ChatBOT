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

import traceback

@app.post("/login")
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
                        # Defensive: check for empty or invalid hash
                        if row_username == username.lower() and row_password_hash:
                            try:
                                if bcrypt.checkpw(password.encode("utf-8"), row_password_hash.encode("utf-8")):
                                    token = sign_token(row_email)
                                    print("✅ Generated token:", token)
                                    print("✅ User authenticated:", username)
                                    response = JSONResponse({
                                        "success": True,
                                        "message": "Login successful.",
                                        "access_token": token,
                                        "token_type": "bearer"
                                    })
                                    # Set SameSite and Secure for better browser compatibility
                                    response.set_cookie(
                                        key="access_token",
                                        value=token,
                                        httponly=True,
                                        path="/",
                                        samesite="lax"
                                    )
                                    return response
                            except ValueError as bcrypt_err:
                                print("❌ Bcrypt value error:", bcrypt_err)
                                continue
                            except Exception as bcrypt_err:
                                print("❌ Bcrypt error:", bcrypt_err)
                                continue
                    except Exception as bcrypt_outer:
                        print("❌ Outer bcrypt error:", bcrypt_outer)
                        continue
            except Exception as e:
                print("❌ CSV read error:", e)
                import traceback
                traceback.print_exc()
                return JSONResponse({"success": False, "message": "Server error reading user database."}, status_code=500)

        return JSONResponse({"success": False, "message": "Invalid username or password."}, status_code=status.HTTP_401_UNAUTHORIZED)

    except Exception as e:
        print("❌ Exception during login:", e)
        traceback.print_exc()  # This prints full stack trace in terminal
        return JSONResponse({"success": False, "message": "An error occurred during login."}, status_code=500)

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
        # Use csv.reader to support both header and no-header CSVs
        reader = csv.reader(f)
        rows = list(reader)
        if not rows:
            return JSONResponse({"success": False, "message": "User database is empty."}, status_code=404)
        # Heuristic: check if first row is header
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
                row["pass•••••••word"] = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
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
    if os.path.exists(csv_path):
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
            if not rows:
                return JSONResponse({"success": True, "users": []})
            # If the first row looks like a header, skip it
            first_row = rows[0]
            # Heuristic: if any cell in the first row contains 'user' or 'email', treat as header
            header_keywords = ['user', 'email', 'contact', 'auth']
            is_header = any(any(key in cell.lower() for key in header_keywords) for cell in first_row)
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
                # Optional: Authentication field
                user["Authentication"] = row[4] if len(row) > 4 else "no"
                # Token used field (6th column, index 5)
                user["token_used"] = row[5] if len(row) > 5 else "0"
                users.append(user)
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
    rows = []
    updated = False
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        all_rows = list(reader)
        # Detect header
        header_keywords = ['user', 'email', 'contact', 'auth', 'token']
        is_header = any(any(key in cell.lower() for key in header_keywords) for cell in all_rows[0]) if all_rows else False
        header = all_rows[0] if is_header else None
        data_rows = all_rows[1:] if is_header else all_rows
        for row in data_rows:
            if len(row) >= 1 and row[0] == username:
                # Ensure row has at least 6 columns (username, email, contact, password, Authentication, token_used)
                while len(row) < 7:
                    row.append("0" if len(row) == 5 else "")
                row[4] = auth_value
                updated = True
            rows.append(row)
    if not updated:
        return JSONResponse({"success": False, "message": "User not found."}, status_code=404)
    # Write back to CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if header:
            writer.writerow(header)
        writer.writerows(rows)
    return JSONResponse({"success": True, "message": "Authentication updated."})

@app.get("/admin_logout")
async def admin_logout():
    response = RedirectResponse(url="/admin", status_code=302)
    response.delete_cookie("admin_logged_in")
    return response