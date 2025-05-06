"""
This module defines the routes and logic for the chat page in a FastAPI application.
============================================================================================
Chat page routes for FastAPI application.

Routes:
- GET /chat: Render the chat page if user is authenticated.
- GET /logout: Logout user and redirect to login page.
- POST /get: Example endpoint for chat response.

Utilities:
- get_current_user_from_cookie(request): Retrieves user from JWT cookie (for demonstration, returns token).
"""

from fastapi import APIRouter, Request, Body
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from inference import LLMChatBot  # Ensure this is the correct import for your chatbot

router = APIRouter()
templates = Jinja2Templates(directory="templates")
chatbot = LLMChatBot()
# Make sure chatbot is defined/imported above
# Example: from chatbot_module import chatbot

def get_current_user_from_cookie(request: Request):
    """
    Retrieve the current user from the JWT access_token cookie.
    (For demonstration, just returns the token. Replace with JWT decode logic for production.)
    """
    token = request.cookies.get("access_token")
    if not token:
        return None
    return token

@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """
    Render the chat page if the user is authenticated.
    """
    user = get_current_user_from_cookie(request)
    if not user:
        response = RedirectResponse(url="/", status_code=302)
        response.delete_cookie("access_token")
        return response
    return templates.TemplateResponse("chat.html", {"request": request, "user": user})

@router.get("/logout")
async def logout():
    """
    Logout the user and redirect to the login page.
    """
    return RedirectResponse(url="/", status_code=302)

@router.post("/get")
async def get_chat_response(request: Request, data: dict = Body(...)):
    """
    Endpoint for POST /get.
    Replace this logic with your actual chat response logic.
    """
    user = get_current_user_from_cookie(request)
    if not user:
        return {"success": False, "message": "Unauthorized"}, 401

    user_msg = data.get("msg", "")
    # Use your inference logic to get the bot reply
    # Make sure chatbot is defined/imported above
    _, result = chatbot.run(user_msg)
    if isinstance(result, dict) and "message" in result:
        return {"reply": result["message"]}
    elif isinstance(result, dict) and "error" in result:
        return {"reply": result["error"]}
    elif hasattr(result, "to_string"):
        return {"reply": result.to_string()}
    else:
        return {"reply": str(result)}