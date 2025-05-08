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
from jwtsign import decode_token  # Make sure this exists or use your JWT decode function
from src.mcp.generate_plot import VisualizationEngine, remove_sensitive_columns
from tabulate import tabulate
import pandas as pd

router = APIRouter()
templates = Jinja2Templates(directory="templates")
chatbot = LLMChatBot()
visualization = VisualizationEngine()

def get_current_user_from_cookie(request: Request):
    """
    Retrieve and validate the current user from the JWT access_token cookie.
    Returns user info if valid, else None.
    """
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        # Replace with your actual JWT decode/validation logic
        user_info = decode_token(token)
        return user_info
    except Exception:
        return None

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
    Enhanced to handle SQL, DataFrame, and visualization output.
    """
    user = get_current_user_from_cookie(request)
    if not user:
        return {"success": False, "message": "Unauthorized"}, 401

    user_msg = data.get("msg", "")
    sql_query, result = chatbot.run(user_msg)

    # Handle error or message responses
    if sql_query == 'N/A' or result is None:
        if isinstance(result, dict) and "message" in result:
            return {"reply": result["message"], "sql": sql_query}
        else:
            return {"reply": "⚠️ Could not process the input.", "sql": sql_query}

    if isinstance(result, dict):
        if "error" in result:
            return {"reply": f"❌ Error: {result['error']}", "sql": sql_query}
        elif "message" in result:
            return {"reply": result["message"], "sql": sql_query}

    # Handle DataFrame results
    if isinstance(result, pd.DataFrame):
        clean_result = remove_sensitive_columns(result)
        output_type = visualization.suggest_output_type(clean_result, user_msg)

        if output_type == 'text':
            # Optionally, implement get_llm_response if available
            # summary = get_llm_response(user_msg, clean_result.to_dict())
            summary = "📝 Insight summary not implemented."
            return {"reply": summary, "sql": sql_query}

        elif output_type == 'table':
            table_str = tabulate(clean_result, headers='keys', tablefmt='pretty')
            return {
                "reply": "📋 Table Output:\n" + table_str,
                "sql": sql_query
            }

        elif output_type == 'plot':
            # Plots can't be sent via JSON; indicate to frontend
            return {
                "reply": "📊 Plot output generated. (Plot display not supported in API response.)",
                "sql": sql_query
            }
        else:
            return {"reply": "⚠️ Unexpected output type.", "sql": sql_query}

    # Fallback for unexpected result format
    return {"reply": str(result), "sql": sql_query}