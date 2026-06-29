import os
import re
import json
import random
import datetime
import wikipedia
wikipedia.set_user_agent("JarvisAIAssistant/2.0 (contact@example.com)")
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
    'who are my friends': ['Your friends are Kushagra Sharma, Vikas Kumar, and Pradeep Sir.'],
    'who is my friend': ['Your friends are Kushagra Sharma, Vikas Kumar, and Pradeep Sir.'],
    'mere friends ke naam bato': ['Your friends are Kushagra Sharma, Vikas Kumar, and Pradeep Sir.'],
    'mere friends ke naam': ['Your friends are Kushagra Sharma, Vikas Kumar, and Pradeep Sir.'],
    'friends ke naam': ['Your friends are Kushagra Sharma, Vikas Kumar, and Pradeep Sir.'],
    'dosto ke naam': ['Your friends are Kushagra Sharma, Vikas Kumar, and Pradeep Sir.'],
    'dost ke naam': ['Your friends are Kushagra Sharma, Vikas Kumar, and Pradeep Sir.'],
    'what is my name': ['Your name is Bhanu (Abhii Abhishek) Sir!'],
    'my name': ['Your name is Bhanu (Abhii Abhishek) Sir!'],
    'your owner': ['Bhanu (Abhii Abhishek Sir)'],
    'who created you': ['I was created by Bhanu Sir, a B.Tech CSE final year student at NGF College of Engineering & Technology, Palwal (affiliated with J.C. Bose University of Science & Technology, YMCA, Faridabad).'],
    'who was created you': ['I was created by Bhanu Sir at NGF College of Engineering & Technology, Palwal.'],
    'bhanu': ['My creator Bhanu is a B.Tech CSE final year student at NGF College, Palwal (affiliated with J.C. Bose University, YMCA). University Roll No: 22035004012, College Roll No: S22cse012. He has completed 7 semesters with a CGPA of 7.216 (68.55%) and is preparing for MBA admissions to premier IIMs.'],
    'who is bhanu': ['My creator Bhanu is a B.Tech CSE final year student at NGF College, Palwal (affiliated with J.C. Bose University, YMCA). University Roll No: 22035004012, College Roll No: S22cse012. He has completed 7 semesters with a CGPA of 7.216 (68.55%) and is preparing for MBA admissions to premier IIMs.'],
    'bhanu bio': ['Bhanu Sir was born on 19th October 2004 in Palwal. He is pursuing B.Tech CSE at J.C. Bose University (YMCA) via NGF College, Palwal. He has a clean academic record with 7.216 CGPA (68.55%) across 7 semesters and aspires to get MBA admission into top IIMs.'],
    'bhanu cgpa': ['Bhanu Sir has achieved an overall CGPA of 7.216 (approximately 68.55%) across 7 completed semesters in B.Tech CSE with a clean academic record.'],
    'bhanu roll number': ['University Roll No: 22035004012 | College Roll No: S22cse012 (B.Tech CSE, NGF College / J.C. Bose University YMCA).'],
    'bhanu college': ['NGF College of Engineering & Technology, Palwal (Affiliated with J.C. Bose University of Science and Technology, YMCA, Faridabad).'],
    'bhanu mba': ['Bhanu Sir is actively preparing for MBA admissions to premier IIMs, including BLACKI and IIM Rohtak!'],
    'how are you': ['I am fine, thank you for asking'],
    'hello': ['Hello Sir, I am ready to assist you.'],
    'thank you jarvis': ['Welcome Sir!'],
    'thank you': ['Welcome Sir!'],
    'introduce': ['I am Jarvis, an Intelligent Multi-Model AI Assistant created by Bhanu Sir for his B.Tech CSE Major Project.'],
    'results': ['Anything else Sir?'],
    'sun': ['The Sun is the star at the center of the Solar System. It is a massive, hot sphere of plasma that provides essential light and energy to Earth.'],
    'moon': ['The Moon is Earth\'s only natural satellite. It orbits Earth and controls ocean tides.'],
    'earth': ['Earth is the third planet from the Sun and the only astronomical object known to harbor life.'],
    'default': ['I am not sure how to respond to that.']
}

class ChatRequest(BaseModel):
    session_id: str
    message: str
    model: str = "gemini-2.5-flash-lite"
    api_key: str | None = None

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

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

    try:
        # Add user message to history
        session["messages"].append({"sender": "user", "text": user_msg, "timestamp": timestamp})
        if session["title"] == "New Chat":
            session["title"] = user_msg[:22]

        # Process response logic
        text_lower = user_msg.lower()
        reply_text = None
        action_url = None

        # Auto-detect personal / friend / event fact statements (ONLY when user is TELLING, not asking)
        is_question = any(w in text_lower for w in ["what", "who", "tell", "when", "kya", "kaun", "kon", "kab", "batao", "bato"])
        if not is_question:
            if any(w in text_lower for w in ["friend", "friends", "dost", "dosto"]) and any(w in text_lower for w in ["birthday", "bday", "janamdin"]):
                save_user_knowledge(f"friend_bday_{datetime.datetime.now().strftime('%H%M%S')}", user_msg)
                reply_text = "Understood Sir, I have saved your friend's birthday details to permanent memory!"
            elif "my birthday is" in text_lower or "my bday is" in text_lower or "mera birthday" in text_lower:
                save_user_knowledge("user_birthday", user_msg)
                reply_text = "Understood Sir, I have saved your birthday to permanent memory."
            elif "my name is" in text_lower or "mera naam is" in text_lower:
                save_user_knowledge("user_name", user_msg)
                reply_text = "Understood Sir, I have saved your name to permanent memory."
            elif "friend" in text_lower or "friends" in text_lower:
                if (" is " in f" {text_lower} " or " are " in f" {text_lower} ") and len(text_lower.split()) > 3:
                    save_user_knowledge(f"fact_{datetime.datetime.now().strftime('%H%M%S')}", user_msg)
                    reply_text = "Understood Sir, I have noted and saved your friends' details to permanent memory."
            elif any(w in text_lower for w in ["practical", "exam", "test", "holiday", "chutti", "event", "meeting", "interview", "presentation", "trip"]) or any(m in text_lower for m in ["july", "august", "september", "october", "november", "december", "january", "february", "march", "april", "may", "june"]):
                if any(k in text_lower for k in ["my", "mera", "meri", "mere", "on", "is", "hai"]):
                    event_id = f"event_{datetime.datetime.now().strftime('%H%M%S')}"
                    save_user_knowledge(event_id, user_msg)
                    reply_text = f"Understood Sir, I have noted and saved your schedule ({user_msg}) to permanent memory!"

        # Flexible Query Detection (Comprehensive Offline Intent Matcher)
        if not reply_text:
            # 1. Assistant Name Queries ("what is your name", "your name", "tera naam", etc.)
            if ("your name" in text_lower or "tera naam" in text_lower or "apka naam" in text_lower or "aapka naam" in text_lower) and not ("my name" in text_lower or "mera naam" in text_lower):
                reply_text = "I am Jarvis, your intelligent AI assistant created by Abhii Abhishek Sir!"
            elif "who are you" in text_lower or "tum kaun ho" in text_lower or "tum kon ho" in text_lower:
                reply_text = "I am Jarvis, your intelligent AI assistant created by Abhii Abhishek Sir!"
            
            # 2. User Friends Queries & Friend Birthdays
            elif any(w in text_lower for w in ["friend", "friends", "dost", "dosto"]) and any(w in text_lower for w in ["birthday", "bday", "brithday", "janamdin", "dates", "date"]):
                knowledge = load_user_knowledge()
                bday_items = [v for k, v in knowledge.items() if "birthday" in k.lower() or "bday" in k.lower() or "birthday" in v.lower() or "bday" in v.lower() or "janamdin" in v.lower()]
                if bday_items:
                    bdays_formatted = "\n• " + "\n• ".join(bday_items)
                    reply_text = f"Here are your saved friend birthday details Sir:{bdays_formatted}"
                else:
                    reply_text = "Your friends are Kushagra Sharma, Vikas Kumar, and Pradeep Sir. You haven't saved specific birthday dates for them yet."
            elif any(w in text_lower for w in ["friend", "friends", "dost", "dosto"]) and any(w in text_lower for w in ["name", "naam", "who", "bato", "batao", "list", "kaun", "kon"]):
                reply_text = "Your friends are Kushagra Sharma, Vikas Kumar, and Pradeep Sir."
            
            # 3. User Name Queries
            elif any(w in text_lower for w in ["mera naam", "my name"]) and any(w in text_lower for w in ["kya", "what", "batao", "bato", "tell"]):
                reply_text = "Your name is Abhii Abhishek Sir!"
            
            # 4. Creator / Owner Queries
            elif any(w in text_lower for w in ["who created", "who made", "owner", "malik", "kisne banaya"]):
                reply_text = "I was created by Abhii Abhishek at NGF College, Palwal Sir!"
            
            # 5. Saved Events / Schedule Queries ("kal kya hai", "agle mahine kya hai", "my schedule", "events")
            elif any(w in text_lower for w in ["schedule", "event", "events", "practical", "exam", "chutti", "holiday", "kaam", "important"]) and any(w in text_lower for w in ["kya", "what", "konsa", "konsi", "batao", "bato", "list", "tell", "show", "agle mahine", "next month", "upcoming"]):
                knowledge = load_user_knowledge()
                event_items = [v for k, v in knowledge.items() if "event" in k or any(w in v.lower() for w in ["practical", "exam", "test", "holiday", "chutti", "event", "meeting"])]
                if event_items:
                    events_formatted = "\n• " + "\n• ".join(event_items)
                    reply_text = f"Here are your saved events & schedules Sir:{events_formatted}"
                else:
                    reply_text = "You don't have any saved events or schedules in permanent memory yet, Sir."

        # Instant Math Calculator Evaluator
        if not reply_text:
            if re.match(r'^\s*[\d\s+\-*/().]+\s*$', text_lower) and any(op in text_lower for op in ['+', '-', '*', '/']):
                try:
                    clean_expr = re.sub(r'[^0-9+\-*/().\s]', '', text_lower)
                    calc_res = eval(clean_expr, {"__builtins__": None}, {})
                    if isinstance(calc_res, (int, float)):
                        formatted_res = f"{int(calc_res)}" if isinstance(calc_res, float) and calc_res.is_integer() else f"{calc_res}"
                        reply_text = f"{user_msg} = {formatted_res}"
                except Exception:
                    pass

        # Predefined checks with top preference matching
        if not reply_text:
            for key in PREDEFINED_RESPONSES:
                if key == 'default':
                    continue
                pattern = r'\b' + re.escape(key) + r'\b'
                if re.search(pattern, text_lower):
                    reply_text = random.choice(PREDEFINED_RESPONSES[key])
                    break

        # Time & Date Queries (Today, Tomorrow, Time in English & Hinglish)
        if not reply_text:
            if any(w in text_lower for w in ["time", "samay", "waqt", "kitne baje"]):
                now_time = datetime.datetime.now().strftime("%I:%M %p")
                reply_text = f"The current time is {now_time}, Sir."
            elif any(w in text_lower for w in ["tomorrow", "kal kya", "kl kya", "kal konsa", "kl konsa", "kal ki date", "kl ki date"]):
                tomorrow_date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%A, %B %d, %Y")
                reply_text = f"Tomorrow will be {tomorrow_date}, Sir."
            elif any(w in text_lower for w in ["today's date", "today date", "aaj konsi date", "aaj ki date"]) or (text_lower.strip() in ["date", "dates", "what date"]):
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
            elif any(w in text_lower for w in ["music", "song", "gaana", "gana", "gane", "geet", "track", "audio"]) and any(w in text_lower for w in ["play", "chalao", "chala", "suno", "sunao", "listen", "start", "plaay"]):
                reply_text = "Playing your favourite music Sir."
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

                now_str = datetime.datetime.now().strftime("%A, %B %d, %Y (%I:%M %p)")
                prompt_parts = [
                    "You are Jarvis, a sleek, intelligent AI assistant created by Abhii Abhishek. "
                    f"Current Live System Date & Time: {now_str}. "
                    "STYLE RULES: Keep responses crisp, stylish, concise, and engaging (in Hinglish/English). Never write long walls of text, boring essays, or textbook lectures. For general advice, give max 3-4 short actionable bullet points with emojis. For coding, give direct code blocks without fluff. "
                    + memory_str
                ]
                recent_turns = session["context"][-10:]
                for turn in recent_turns:
                    role_str = "User" if turn["role"] == "user" else "Jarvis"
                    prompt_parts.append(f"{role_str}: {turn['content']}")
                prompt_parts.append(f"User: {user_msg}\nJarvis:")

                response = None
                models_to_try = [req.model, "gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]
                for m_name in models_to_try:
                    try:
                        resp = active_client.models.generate_content(
                            model=m_name,
                            contents="\n".join(prompt_parts),
                            config=types.GenerateContentConfig(max_output_tokens=350, temperature=0.7)
                        )
                        if resp and hasattr(resp, 'text') and resp.text:
                            response = resp
                            break
                    except Exception as try_err:
                        print(f"[Model Retry {m_name}] {try_err}")

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
                is_task_request = any(w in text_lower for w in ["make", "write", "create", "generate", "draft", "banao", "likho", "tayyar"])
                if is_task_request:
                    if any(w in text_lower for w in ["letter", "patra", "chitti", "application", "mail", "email"]):
                        reply_text = (
                            "Here is a formal letter template for you Sir:\n\n"
                            "[Date]\nTo, [Recipient Name/Title]\n[Company/Organization]\n\n"
                            "Subject: Formal Request / Application\n\n"
                            "Dear Sir/Madam,\n\n"
                            "I am writing this letter to formally bring to your attention regarding...\n\n"
                            "Thanking you,\nSincerely,\n[Your Name]"
                        )
                    else:
                        reply_text = "I would be glad to generate custom content for you Sir! However, custom text generation requires an active Gemini AI connection. Please add a new API key in Settings so I can generate custom content for you!"
                else:
                    try:
                        clean_q = re.sub(r'\b(what|who|where|when|is|are|tell|me|about|the|a|an|in|of|ka|ki|ke|ko|batao|bato|kon|hai|kya|sir|plz|please)\b', '', user_msg, flags=re.IGNORECASE).strip()
                        search_q = clean_q if len(clean_q) >= 2 else user_msg
                        search_results = wikipedia.search(search_q)
                        target_topic = search_results[0] if search_results else search_q
                        try:
                            wiki_summary = wikipedia.summary(target_topic, sentences=2, auto_suggest=False)
                        except wikipedia.exceptions.DisambiguationError as de:
                            wiki_summary = wikipedia.summary(de.options[0], sentences=2, auto_suggest=False)
                        reply_text = f"According to Wikipedia: {wiki_summary}"
                    except Exception as w_err:
                        print(f"[Offline Wiki Search Fail] {w_err}")
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
    except Exception as master_err:
        print(f"[Master Process Chat Error] {master_err}")
        err_reply = "Hello Sir, standing by for commands."
        return {
            "reply": err_reply,
            "action_url": None,
            "api_status": "offline",
            "timestamp": timestamp,
            "session": session
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
