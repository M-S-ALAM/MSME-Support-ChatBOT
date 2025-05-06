from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_current_user_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    # You may want to import and use your JWT decode logic here
    # For now, just return token for demonstration
    return token

@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    user = get_current_user_from_cookie(request)
    if not user:
        response = RedirectResponse(url="/", status_code=302)
        response.delete_cookie("access_token")
        return response
    return templates.TemplateResponse("chat.html", {"request": request, "user": user})

@router.get("/logout")
async def logout():
    return RedirectResponse(url="/", status_code=302)