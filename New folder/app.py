import os
import random
import datetime
import wikipedia
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from google import genai

app = FastAPI(title="Jarvis AI Assistant Cloud API")

# Setup templates directory
templates = Jinja2Templates(directory="templates")

# In-memory session store (or persistent dict)
sessions_db = {}

# Setup Gemini AI Client
API_KEY = os.environ.get("GEMINI_API_KEY", "")
gemini_client = None
if API_KEY:
    try:
        gemini_client = genai.Client(api_key=API_KEY)
    except Exception as e:
        print(f"[Gemini Init Warning] {e}")

PREDEFINED_RESPONSES = {
    'hi': ['Hello! Sir, I am ready to assist you.', 'Hi sir, how can I help you today?'],
    'greetings': ['Hello! Sir, I am ready to assist you.'],
    'my friends name': ['Vikas Kumar, Kushagra, and Pradeep.'],
    'your owner': ['Abhii Abhishek and Bhanu Pratap Singh.'],
    'how are you': ['I am operating at peak efficiency, thank you Sir!'],
    'hello': ['Hello Sir, standing by for commands.'],
    'thank you': ['You are most welcome, Sir!'],
    'introduce': ['I am Jarvis, an advanced AI virtual assistant designed to process commands, search the web, and answer complex questions.'],
    'who created you': ['I was created by Abhii Abhishek at NGF College, Palwal.']
}

class ChatRequest(BaseModel):
    session_id: str
    message: str
    model: str = "gemini-2.5-flash"

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/sessions")
async def get_sessions():
    return list(sessions_db.values())

@app.post("/api/new_chat")
async def new_chat():
    sid = datetime.datetime.now().strftime("chat_%Y%m%d_%H%M%S")
    session_data = {
        "id": sid,
        "title": "New Chat",
        "messages": [],
        "context": []
    }
    sessions_db[sid] = session_data
    return session_data

@app.delete("/api/sessions")
async def clear_all_history():
    sessions_db.clear()
    return {"status": "success"}

@app.post("/api/chat")
async def process_chat(req: ChatRequest):
    sid = req.session_id
    if sid not in sessions_db:
        sessions_db[sid] = {
            "id": sid,
            "title": "New Chat",
            "messages": [],
            "context": []
        }

    session = sessions_db[sid]
    user_msg = req.message.strip()
    timestamp = datetime.datetime.now().strftime("%H:%M")

    # Add user message to history
    session["messages"].append({"sender": "user", "text": user_msg, "timestamp": timestamp})
    if session["title"] == "New Chat":
        session["title"] = user_msg[:22]

    # Process response logic
    text_lower = user_msg.lower()
    reply_text = None

    # Predefined checks
    for key in PREDEFINED_RESPONSES:
        if key in text_lower:
            reply_text = random.choice(PREDEFINED_RESPONSES[key])
            break

    # Wikipedia queries
    if not reply_text and "wikipedia" in text_lower:
        query = user_msg.replace("wikipedia", "").replace("search", "").strip()
        if query:
            try:
                result = wikipedia.summary(query, sentences=2)
                reply_text = f"According to Wikipedia: {result}"
            except Exception:
                reply_text = "Sorry Sir, I couldn't fetch Wikipedia results."

    # Gemini AI
    if not reply_text and gemini_client:
        try:
            prompt_parts = [
                "You are Jarvis, a sleek, intelligent AI assistant created by Abhii Abhishek. "
                "Respond concisely and helpfully in 1-3 sentences without markdown headers or bullet points."
            ]
            recent_turns = session["context"][-10:]
            for turn in recent_turns:
                role_str = "User" if turn["role"] == "user" else "Jarvis"
                prompt_parts.append(f"{role_str}: {turn['content']}")
            prompt_parts.append(f"User: {user_msg}\nJarvis:")

            response = gemini_client.models.generate_content(
                model=req.model,
                contents="\n".join(prompt_parts)
            )
            if response and hasattr(response, 'text') and response.text:
                reply_text = response.text.strip()
        except Exception as e:
            print(f"[Gemini Error] {e}")

    if not reply_text:
        reply_text = "Sorry Sir, I am currently operating in offline mode."

    # Record context & assistant reply
    session["context"].append({"role": "user", "content": user_msg})
    session["context"].append({"role": "assistant", "content": reply_text})
    session["messages"].append({"sender": "bot", "text": reply_text, "timestamp": timestamp})

    return {
        "reply": reply_text,
        "timestamp": timestamp,
        "session": session
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
