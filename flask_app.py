from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import pandas as pd
from inference import LLMChatBot
from modular_code.config import ChatGPTConfig
from modular_code.utils.constant import UI_constants, OpenAIConfig
from openai import OpenAI
from visualization_plot import VisualizationEngine

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

bot = LLMChatBot()
llm_client = OpenAI(api_key=ChatGPTConfig.API_KEY)
engine = VisualizationEngine()

class ChatRequest(BaseModel):
    message: str

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.post("/chat")
def chat(request: ChatRequest):
    user_input = request.message
    if not user_input:
        return JSONResponse(content={"error": "No message provided."}, status_code=400)

    try:
        sql_query, result = bot.run(user_input)
        sanitized_result = remove_sensitive_columns(result)

        if isinstance(sanitized_result, pd.DataFrame):
            if sanitized_result.shape == (1, 1):
                val = sanitized_result.iloc[0, 0]
                llm_text = get_llm_response(user_input, val)
                return {"type": "text", "content": llm_text}
            else:
                table_html = sanitized_result.to_html(index=False)
                print(table_html)
                return {"type": "table", "content": table_html}
        elif isinstance(sanitized_result, dict):
            return {"type": "text", "content": sanitized_result.get("message", "Error occurred.")}
        else:
            return {"type": "text", "content": "Sorry, no valid response from database."}
    except Exception as e:
        return {"type": "error", "content": str(e)}

def get_llm_response(query, value):
    prompt = f"The user asked: '{query}'. The result from the database is '{value}'. Provide a simple summary."
    try:
        response = llm_client.chat.completions.create(
            model=OpenAIConfig.OpenAI_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant providing insights based on database query results."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=OpenAIConfig.OpenAI_max_tokens,
            temperature=OpenAIConfig.OpenAI_temperature,
            top_p=OpenAIConfig.OpenAI_top_p
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Failed to generate insight: {e}"

def remove_sensitive_columns(result):
    columns_to_remove = {
        "customer_id", "employee_id", "project_id", "department_id",
        "invoice_id", "payment_id", "task_id", "time_entry_id"
    }
    if isinstance(result, pd.DataFrame):
        return result.drop(columns=[col for col in columns_to_remove if col in result.columns], errors='ignore')
    elif isinstance(result, list) and result and isinstance(result[0], dict):
        return [{k: v for k, v in row.items() if k not in columns_to_remove} for row in result]
    return result
