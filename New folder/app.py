import os
import json
import random
import datetime
import wikipedia
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from google import genai
from google.genai import types

app = FastAPI(title="Jarvis AI Assistant Cloud API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates directory using absolute script path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# In-memory session store & Global knowledge file
sessions_db = {}
KNOWLEDGE_FILE = os.path.join(BASE_DIR, "user_knowledge.json")

def load_user_knowledge():
    if os.path.exists(KNOWLEDGE_FILE):
        try:
            with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_user_knowledge(key, val):
    data = load_user_knowledge()
    data[key] = val
    try:
        with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Save Knowledge Error] {e}")

# Setup Gemini AI Client
API_KEY = os.environ.get("GEMINI_API_KEY", "")
gemini_client = None
if API_KEY:
    try:
        gemini_client = genai.Client(api_key=API_KEY)
    except Exception as e:
        print(f"[Gemini Init Warning] {e}")

PREDEFINED_RESPONSES = {
    'hi': ['Hello! Sir, I am ready to assist you.', 'Hi sir, I am ready to assist you.', 'Hello Sir, I am ready to assist you.'],
    'hey': ['Hello! Sir, I am ready to assist you.', 'Hey Sir, how can I help you today?', 'Hello Sir, standing by.'],
    'greetings': ['Hello! Sir, I am ready to assist you.', 'Hi sir, I am ready to assist you.', 'Hello Sir, I am ready to assist you.'],
    'my friends name': ['Vikas Kumar, Kushagra', 'Pradeep'],
    'your owner': ['Abhii Abhishek', 'Bhanu Pratap Singh'],
    'how are you': ['I am fine, thank you for asking'],
    'hello': ['Hello Sir, I am ready to assist you.'],
    'thank you jarvis': ['Welcome Sir!'],
    'thank you': ['Welcome Sir!'],
    'introduce': ['I am a computer program chatbot AI that can understand and respond to human speech.I was created by Abhii AbhishIek . I am named after the character Jarvis from the Iron Man movies.'],
    'who created you': ['I was created by Abhii Abhishek at NGF College, Palwal.'],
    'who was created you': ['I was created by Abhii Abhishek at NGF College, Palwal.'],
    'results': ['Anything else Sir?'],
    'default': ['I am not sure how to respond to that.']
}

class ChatRequest(BaseModel):
    session_id: str
    message: str
    model: str = "gemini-2.5-flash"
    api_key: str = None

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

@app.delete("/api/session/{sid}")
async def delete_single_session(sid: str):
    if sid in sessions_db:
        del sessions_db[sid]
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
    action_url = None

    # Auto-detect personal / friend fact statements
    if "birthday" in text_lower or "friends" in text_lower or "friend" in text_lower or "my name" in text_lower:
        if "my birthday" in text_lower or "my bday" in text_lower:
            save_user_knowledge("user_birthday", user_msg)
        else:
            save_user_knowledge(f"fact_{datetime.datetime.now().strftime('%H%M%S')}", user_msg)

    # Predefined checks with exact word boundary matching (avoids matching 'hi' in 'his')
    for key in PREDEFINED_RESPONSES:
        pattern = r'\b' + re.escape(key) + r'\b'
        if re.search(pattern, text_lower):
            reply_text = random.choice(PREDEFINED_RESPONSES[key])
            break

    # Time & Date Queries
    if not reply_text:
        if "time" in text_lower or "current time" in text_lower or "what time" in text_lower:
            now_time = datetime.datetime.now().strftime("%I:%M %p")
            reply_text = f"The current time is {now_time}, Sir."
        elif "date" in text_lower or "today's date" in text_lower or "what date" in text_lower:
            now_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
            reply_text = f"Today's date is {now_date}, Sir."

    # Actionable Tasks
    if not reply_text:
        if "open youtube" in text_lower:
            reply_text = "Opening YouTube Sir."
            action_url = "https://www.youtube.com"
        elif "open google" in text_lower:
            reply_text = "Opening Google Sir."
            action_url = "https://www.google.com"
        elif "play music" in text_lower or "play song" in text_lower or "favourite song" in text_lower or "favorite song" in text_lower:
            reply_text = "Playing your favourite song Sir."
            action_url = "https://www.youtube.com/watch?v=r03GO2AlNUo&t=26s"
        elif "open amazon" in text_lower:
            reply_text = "Opening Amazon Sir."
            action_url = "https://www.amazon.com"

    # Wikipedia queries
    if not reply_text and "wikipedia" in text_lower:
        query = user_msg.replace("wikipedia", "").replace("search", "").strip()
        if query:
            try:
                result = wikipedia.summary(query, sentences=2)
                reply_text = f"According to Wikipedia: {result}"
            except Exception:
                reply_text = "Sorry Sir, I couldn't fetch Wikipedia results."

    # Gemini AI Status tracking
    active_client = gemini_client
    if req.api_key and req.api_key.strip():
        try:
            active_client = genai.Client(api_key=req.api_key.strip())
        except Exception as e:
            print(f"[Custom API Key Client Error] {e}")

    api_status = "online" if active_client else "offline"

    if not reply_text and active_client:
        try:
            global_memories = load_user_knowledge()
            memory_str = ""
            if global_memories:
                memory_str = "Permanent User Knowledge/Facts: " + json.dumps(global_memories, ensure_ascii=False) + ". Use this knowledge when answering questions about the user."

            prompt_parts = [
                "You are Jarvis, a sleek, intelligent AI assistant created by Abhii Abhishek. "
                "Respond concisely and helpfully in 1-3 sentences without markdown headers or bullet points. "
                + memory_str
            ]
            recent_turns = session["context"][-10:]
            for turn in recent_turns:
                role_str = "User" if turn["role"] == "user" else "Jarvis"
                prompt_parts.append(f"{role_str}: {turn['content']}")
            prompt_parts.append(f"User: {user_msg}\nJarvis:")

            response = active_client.models.generate_content(
                model=req.model,
                contents="\n".join(prompt_parts),
                config=types.GenerateContentConfig(max_output_tokens=150, temperature=0.7)
            )
            if response and hasattr(response, 'text') and response.text:
                reply_text = response.text.strip()
                api_status = "online"
            else:
                api_status = "offline"
        except Exception as e:
            print(f"[Gemini Error] {e}")
            api_status = "offline"

    if not reply_text:
        if api_status == "offline":
            reply_text = "Sorry Sir, Gemini AI limit reached or offline. Operating in predefined command mode."
        else:
            reply_text = "I am not sure how to respond to that Sir."

    # Record context & assistant reply
    session["context"].append({"role": "user", "content": user_msg})
    session["context"].append({"role": "assistant", "content": reply_text})
    session["messages"].append({"sender": "bot", "text": reply_text, "timestamp": timestamp})

    return {
        "reply": reply_text,
        "action_url": action_url,
        "api_status": api_status,
        "timestamp": timestamp,
        "session": session
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
