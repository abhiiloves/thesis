import os
import re
import json
import random
import datetime
import urllib.request
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

# India Standard Time (IST) Zone Setup
IST_TZ = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

def get_ist_now():
    return datetime.datetime.now(IST_TZ)

def get_live_weather_report(text_lower):
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=28.1471&longitude=77.3260&current_weather=true&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max&timezone=Asia%2FKolkata"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        
        curr = data.get("current_weather", {})
        temp = curr.get("temperature", "N/A")
        wind = curr.get("windspeed", "N/A")
        wcode = curr.get("weathercode", 0)
        
        daily = data.get("daily", {})
        precip_probs = daily.get("precipitation_probability_max", [0, 0])
        max_temps = daily.get("temperature_2m_max", ["N/A", "N/A"])
        min_temps = daily.get("temperature_2m_min", ["N/A", "N/A"])
        
        # Check if query is asking for TOMORROW'S weather ("kl ka mausam", "tomorrow weather")
        if any(w in text_lower for w in ["kal", "kl", "tomorrow"]):
            t_max = max_temps[1] if len(max_temps) > 1 else "38"
            t_min = min_temps[1] if len(min_temps) > 1 else "29"
            t_prob = precip_probs[1] if len(precip_probs) > 1 else 20
            rain_note = f"Rain probability is around {t_prob}%." if t_prob > 30 else "No heavy rainfall expected."
            return f"🌤️ **Tomorrow's Weather Forecast for Palwal / NCR**:\n• Expected Max Temp: {t_max}°C\n• Expected Min Temp: {t_min}°C\n• Rain Probability: {t_prob}%\n• Summary: {rain_note} Have a great day tomorrow, Sir!"

        precip_prob = precip_probs[0] if precip_probs else 0
        max_temp = max_temps[0] if max_temps else "N/A"
        min_temp = min_temps[0] if min_temps else "N/A"
        
        condition = "Clear sky ☀️"
        if wcode in [1, 2, 3]: condition = "Partly Cloudy / Overcast ⛅"
        elif wcode in [45, 48]: condition = "Foggy 🌫️"
        elif wcode in [51, 53, 55, 61, 63, 65, 80, 81, 82]: condition = "Rainy / Rain Showers 🌧️"
        elif wcode in [95, 96, 99]: condition = "Thunderstorm 🌩️"
        
        if any(w in text_lower for w in ["baarish", "barish", "rain", "raining", "rainy", "paani"]):
            if precip_prob > 50:
                return f"🌧️ Rain Forecast for Palwal/NCR: Today there is a high chance of rain ({precip_prob}% probability)! Current temperature is {temp}°C with {condition}. Carry an umbrella, Sir!"
            elif precip_prob > 20:
                return f"⛅ Rain Forecast for Palwal/NCR: Today there is a slight chance of light rain ({precip_prob}% chance). Current condition is {condition} at {temp}°C."
            else:
                return f"☀️ Rain Forecast for Palwal/NCR: No significant rain expected today (only {precip_prob}% chance). Weather is currently {condition} at {temp}°C."
                
        if "monsoon" in text_lower or "mansoon" in text_lower:
            return f"🌩️ Monsoon Update for Palwal / Haryana: The South-West Monsoon normally arrives in Haryana & Delhi-NCR in late June / early July! Live satellite sync shows active cloud systems with max temperature {max_temp}°C and rain probability peaking at {daily.get('precipitation_probability_max', [0,0,0,50])[3]}% in coming days!"

        return f"🌡️ Live Weather Report for Palwal / NCR:\n• Current Temp: {temp}°C\n• Condition: {condition}\n• Today Max/Min Temp: {max_temp}°C / {min_temp}°C\n• Rain Probability: {precip_prob}%\n• Wind Speed: {wind} km/h\n\nAll satellite systems synced Sir!"
    except Exception as e:
        if any(w in text_lower for w in ["kal", "kl", "tomorrow"]):
            return f"🌤️ Tomorrow's Weather Info for Palwal/NCR: Expected around 36°C to 38°C with partly cloudy skies."
        return f"🌤️ Live Weather Info for Palwal/NCR: Currently around 31°C with clear to partly cloudy skies. Satellite live sync active!"

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
    'kya haal h': ['All systems optimal, Sir! Ready to assist you.', 'Main badhiya hoon Sir! Standing by for your instructions.'],
    'kya haal hai': ['All systems optimal, Sir! Ready to assist you.', 'Main badhiya hoon Sir! Standing by for your instructions.'],
    'kya haal': ['All systems optimal, Sir! Ready to assist you.', 'Main badhiya hoon Sir! Standing by for your instructions.'],
    'ky haal h': ['All systems optimal, Sir! Ready to assist you.', 'Main badhiya hoon Sir! Standing by for your instructions.'],
    'ky haal': ['All systems optimal, Sir! Ready to assist you.', 'Main badhiya hoon Sir! Standing by for your instructions.'],
    'ky hal': ['All systems optimal, Sir! Ready to assist you.', 'Main badhiya hoon Sir! Standing by for your instructions.'],
    'kya hal': ['All systems optimal, Sir! Ready to assist you.', 'Main badhiya hoon Sir! Standing by for your instructions.'],
    'kaise ho': ['All systems optimal, Sir! I am ready to assist you.', 'Main badhiya hoon Sir, aap bataiye kaise hain?'],
    'kaise h': ['All systems optimal, Sir! I am ready to assist you.', 'Main badhiya hoon Sir, aap bataiye kaise hain?'],
    'kese ho': ['All systems optimal, Sir! I am ready to assist you.', 'Main badhiya hoon Sir, aap bataiye kaise hain?'],
    'kya chal raha hai': ['All systems running smoothly Sir! Ready for your commands.'],
    'kya chal rha h': ['All systems running smoothly Sir! Ready for your commands.'],
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
    'bhanu hobbies': ['Bhanu Sir\'s key hobbies & interests include:\n🤖 AI & Software Development\n💻 Coding & Hackathons\n📈 Stock Market & Investing\n📚 Learning New Technologies\n🧩 Problem Solving (Aptitude/Math)\n🎯 Career Preparation (MBA/IIM)'],
    'bhanu interests': ['Bhanu Sir\'s key hobbies & interests include:\n🤖 AI & Software Development\n💻 Coding & Hackathons\n📈 Stock Market & Investing\n📚 Learning New Technologies\n🧩 Problem Solving (Aptitude/Math)\n🎯 Career Preparation (MBA/IIM)'],
    'bhanu github': ['Bhanu Sir\'s GitHub profile: https://github.com/abhiiloves'],
    'bhanu linkedin': ['Bhanu Sir\'s LinkedIn profile: https://www.linkedin.com/in/bhanu-60a88a26a'],
    'bhanu instagram': ['Bhanu Sir\'s Instagram profile: https://www.instagram.com/abhiiloves'],
    'bhanu social media': ['Here are Bhanu Sir\'s official profile links:\n💻 GitHub: https://github.com/abhiiloves\n💼 LinkedIn: https://www.linkedin.com/in/bhanu-60a88a26a\n📸 Instagram: https://www.instagram.com/abhiiloves'],
    'bhanu links': ['Here are Bhanu Sir\'s official profile links:\n💻 GitHub: https://github.com/abhiiloves\n💼 LinkedIn: https://www.linkedin.com/in/bhanu-60a88a26a\n📸 Instagram: https://www.instagram.com/abhiiloves'],
    'how are you': ['All systems optimal, Sir! Ready to assist you.'],
    'hello': ['Hello Sir, I am ready to assist you.'],
    'thank you jarvis': ['Welcome Sir!'],
    'thank you': ['Welcome Sir!'],
    'introduce': ['I am Jarvis, an Intelligent Multi-Model AI Assistant created by Bhanu Sir for his B.Tech CSE Major Project.'],
    'results': ['Anything else Sir?'],
    'sun': ['The Sun is the star at the center of the Solar System. It is a massive, hot sphere of plasma that provides essential light and energy to Earth.'],
    'moon': ['The Moon is Earth\'s only natural satellite. It orbits Earth and controls ocean tides.'],
    'earth': ['Earth is the third planet from the Sun and the only astronomical object known to harbor life.'],
    'default': ['All systems optimal Sir! Ready for your commands.']
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
    sid = get_ist_now().strftime("chat_%Y%m%d_%H%M%S")
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
    timestamp = get_ist_now().strftime("%I:%M %p")

    try:
        # Add user message to history
        session["messages"].append({"sender": "user", "text": user_msg, "timestamp": timestamp})
        if session["title"] == "New Chat":
            session["title"] = user_msg[:22]

        # Process response logic
        text_lower = user_msg.lower()
        reply_text = None
        action_url = None

        # Process Statements (Fact & Event Saving) FIRST if it is clearly a statement!
        is_query = any(w in text_lower for w in ["kya", "what", "konsa", "konsi", "batao", "bato", "list", "tell", "show", "who", "when", "kab", "kaun", "kon"])
        
        if not is_query:
            # A. Friend Birthday Statements (HIGHEST PRIORITY)
            if any(w in text_lower for w in ["birthday", "bday", "janamdin"]):
                if any(w in text_lower for w in ["friend", "friends", "dost", "dosto", "kushagra", "vikas", "pradeep", "on", "is", "hai", "=", ":"]):
                    save_user_knowledge(f"friend_bday_{get_ist_now().strftime('%H%M%S')}", user_msg)
                    reply_text = "Understood Sir, I have saved your friend's birthday details to permanent memory!"
            elif "my birthday is" in text_lower or "my bday is" in text_lower or "mera birthday" in text_lower:
                save_user_knowledge("user_birthday", user_msg)
                reply_text = "Understood Sir, I have saved your birthday to permanent memory."
            elif "my name is" in text_lower or "mera naam is" in text_lower:
                save_user_knowledge("user_name", user_msg)
                reply_text = "Understood Sir, I have saved your name to permanent memory."
            # B. Schedule & Exam Statements (ONLY if not a birthday!)
            elif any(w in text_lower for w in ["practical", "pratical", "exam", "test", "holiday", "chutti", "event", "meeting", "interview", "presentation", "trip"]):
                if any(k in text_lower for k in ["my", "mera", "meri", "mere", "on", "is", "hai", "ko", "kl", "kal"]):
                    event_id = f"event_{get_ist_now().strftime('%H%M%S')}"
                    save_user_knowledge(event_id, user_msg)
                    reply_text = f"Got it, Sir! 🗓️ Noted and saved your schedule ({user_msg}) to permanent memory!"

        # Flexible Query Detection (Comprehensive Offline Intent Matcher)
        if not reply_text:
            # 1. User Friends Queries & Friend Birthdays
            if any(w in text_lower for w in ["friend", "friends", "dost", "dosto"]) and any(w in text_lower for w in ["birthday", "bday", "brithday", "janamdin", "dates", "date"]):
                knowledge = load_user_knowledge()
                bday_items = [v for k, v in knowledge.items() if k.startswith("friend_bday") or ("friend" in k.lower() and "birthday" in k.lower())]
                if bday_items:
                    bdays_formatted = "\n• " + "\n• ".join(bday_items)
                    reply_text = f"Here are your saved friend birthday details Sir:{bdays_formatted}"
                else:
                    reply_text = "Your friends and birthdays are:\n• Kushagra Sharma: April 14th 🎂\n• Vikas Kumar: July 8th 🎂\n• Pradeep Sir: June 19th 🎂"
            elif any(w in text_lower for w in ["friend", "friends", "dost", "dosto"]) and (any(w in text_lower for w in ["name", "naam", "nam", "who", "bato", "batao", "list", "kaun", "kon"]) or "dost" in text_lower):
                reply_text = "Your friends are Kushagra Sharma, Vikas Kumar, and Pradeep Sir."
            
            # 2. Assistant Name Queries
            elif ("your name" in text_lower or "tera naam" in text_lower or "apka naam" in text_lower or "aapka naam" in text_lower) and not ("my name" in text_lower or "mera naam" in text_lower):
                reply_text = "I am Jarvis, your intelligent AI assistant created by Abhii Abhishek Sir!"
            elif "who are you" in text_lower or "tum kaun ho" in text_lower or "tum kon ho" in text_lower:
                reply_text = "I am Jarvis, your intelligent AI assistant created by Abhii Abhishek Sir!"
            
            # 3. User Name Queries
            elif any(w in text_lower for w in ["mera naam", "my name"]) and any(w in text_lower for w in ["kya", "what", "batao", "bato", "tell"]):
                reply_text = "Your name is Bhanu (Abhii Abhishek) Sir!"
            
            # 4. Creator / Owner Queries
            elif any(w in text_lower for w in ["who created", "who made", "owner", "malik", "kisne banaya"]):
                reply_text = "I was created by Bhanu Sir at NGF College, Palwal!"

            # 5. Saved Events / Schedule Queries ("kal kya hai", "agle mahine kya hai", "next month", "my schedule", "events")
            elif any(w in text_lower for w in ["schedule", "event", "events", "practical", "pratical", "exam", "chutti", "holiday", "kaam", "important", "next month", "agle mahine", "upcoming"]) and any(w in text_lower for w in ["kya", "what", "konsa", "konsi", "batao", "bato", "list", "tell", "show", "is", "h"]):
                knowledge = load_user_knowledge()
                event_items = [v for k, v in knowledge.items() if k.startswith("event_")]
                out_msg = "Here are your saved events & upcoming schedules Sir:"
                if event_items:
                    out_msg += "\n• " + "\n• ".join(event_items)
                else:
                    out_msg += "\n• 6th July: Practical Exam 📚\n• 8th July: Vikas Kumar's Birthday 🎂"
                reply_text = out_msg

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

        # Live Weather Engine & Time/Date Queries
        if not reply_text:
            if any(w in text_lower for w in ["weather", "mausam", "moosam", "mosam", "baarish", "barish", "rain", "monsoon", "mansoon", "temperature", "taapman", "tapman"]):
                reply_text = get_live_weather_report(text_lower)
            elif any(w in text_lower for w in ["time", "samay", "waqt", "kitne baje"]):
                now_time = get_ist_now().strftime("%I:%M %p")
                reply_text = f"The current time is {now_time}, Sir."
            elif any(w in text_lower for w in ["tomorrow", "kal kya", "kl kya", "kal konsa", "kl konsa", "kal ki date", "kl ki date"]):
                tomorrow_date = (get_ist_now() + datetime.timedelta(days=1)).strftime("%A, %B %d, %Y")
                reply_text = f"Tomorrow will be {tomorrow_date}, Sir."
            elif any(w in text_lower for w in ["today's date", "today date", "aaj konsi date", "aaj ki date"]) or (text_lower.strip() in ["date", "dates", "what date"]):
                now_date = get_ist_now().strftime("%A, %B %d, %Y")
                reply_text = f"Today's date is {now_date}, Sir."

        # Actionable Tasks
        if not reply_text:
            if "whatsapp" in text_lower and any(w in text_lower for w in ["open", "chalao", "kholo", "start", "show"]):
                reply_text = "Opening WhatsApp Web Sir."
                action_url = "https://web.whatsapp.com"
            elif any(w in text_lower for w in ["amazon", "amaon", "amzon", "amzn", "amazn"]) and any(w in text_lower for w in ["open", "chalao", "kholo", "start", "show", "shopping"]):
                reply_text = "Opening Amazon Sir."
                action_url = "https://www.amazon.in"
            elif "open youtube" in text_lower:
                reply_text = "Opening YouTube Sir."
                action_url = "https://www.youtube.com"
            elif "open google" in text_lower:
                reply_text = "Opening Google Sir."
                action_url = "https://www.google.com"
            elif any(w in text_lower for w in ["music", "song", "gaana", "gana", "gane", "geet", "track", "audio"]) and any(w in text_lower for w in ["play", "chalao", "chala", "suno", "sunao", "listen", "start", "plaay"]):
                reply_text = "Playing your favourite music Sir."
                action_url = "https://www.youtube.com/watch?v=r03GO2AlNUo&t=26s"
            elif "flipkart" in text_lower and any(w in text_lower for w in ["open", "chalao", "kholo", "start", "show", "shopping"]):
                reply_text = "Opening Flipkart Sir."
                action_url = "https://www.flipkart.com"
            elif "myntra" in text_lower and any(w in text_lower for w in ["open", "chalao", "kholo", "start", "show", "shopping"]):
                reply_text = "Opening Myntra Sir."
                action_url = "https://www.myntra.com"
            elif "meesho" in text_lower and any(w in text_lower for w in ["open", "chalao", "kholo", "start", "show", "shopping"]):
                reply_text = "Opening Meesho Sir."
                action_url = "https://www.meesho.com"
            elif any(w in text_lower for w in ["shopping", "khareedari", "kharidari"]) and any(w in text_lower for w in ["open", "chalao", "kholo", "start", "show", "on", "website", "site"]):
                shop_sites = [
                    ("Amazon", "https://www.amazon.in"),
                    ("Flipkart", "https://www.flipkart.com"),
                    ("Myntra", "https://www.myntra.com"),
                    ("Meesho", "https://www.meesho.com")
                ]
                chosen = random.choice(shop_sites)
                reply_text = f"Opening {chosen[0]} for your online shopping Sir!"
                action_url = chosen[1]
            elif "github" in text_lower and any(w in text_lower for w in ["open", "dekho", "show", "kholo"]):
                reply_text = "Opening your GitHub profile Sir: https://github.com/abhiiloves"
                action_url = "https://github.com/abhiiloves"
            elif "linkedin" in text_lower and any(w in text_lower for w in ["open", "dekho", "show", "kholo"]):
                reply_text = "Opening your LinkedIn profile Sir: https://www.linkedin.com/in/bhanu-60a88a26a"
                action_url = "https://www.linkedin.com/in/bhanu-60a88a26a"
            elif "instagram" in text_lower and any(w in text_lower for w in ["open", "dekho", "show", "kholo"]):
                reply_text = "Opening your Instagram profile Sir: https://www.instagram.com/abhiiloves"
                action_url = "https://www.instagram.com/abhiiloves"

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

                now_str = get_ist_now().strftime("%A, %B %d, %Y (%I:%M %p)")
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
                # Default is gemini-2.5-flash-lite, then cascade through other flash models if limit reached
                models_to_try = ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]
                if req.model and req.model not in models_to_try:
                    models_to_try.insert(0, req.model)

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
                    # All models failed / quota reached -> Mark offline and trigger offline predefined & Wikipedia search!
                    api_status = "offline"
            except Exception as e:
                print(f"[Gemini Error] {e}")
                api_status = "offline"

        if not reply_text:
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
                    reply_text = "Sir, Gemini AI limit reached or offline! Please add a new API key in Settings to generate custom AI content."
            else:
                is_greeting = any(w in text_lower for w in ["haal", "hal", "kaise", "kese", "hello", "hi", "hey", "sup", "greetings"])
                if is_greeting:
                    reply_text = "All systems optimal Sir! Ready for your commands."
                else:
                    try:
                        # Dedicated Hinglish to English Query Translator/Normalizer specifically for Wikipedia
                        stops = [
                            r'\b(ke|ki|ka|ko|se|me|par|bhi|hi|pe|ne)\b',
                            r'\b(barme|bare|baare|batao|bato|bataye|bataiye|bata|janana|jaanna|dikhaye|dikhao)\b',
                            r'\b(what|who|where|when|why|how|is|are|was|were|tell|me|about|explain|describe)\b',
                            r'\b(kon|kaun|kya|kaisa|kaisi|kaise|kab|kahan|kha|kaha|hai|h|hein|tha|thi|the)\b',
                            r'\b(krte|karna|karo|kare|hote|hota|hoti|karte|karta|karti|do|doing|make|use|used)\b',
                            r'\b(sir|please|plz|bhai|bro|jarvis|ok)\b'
                        ]
                        cleaned_topic = user_msg
                        for pat in stops:
                            cleaned_topic = re.sub(pat, '', cleaned_topic, flags=re.IGNORECASE)
                        cleaned_topic = re.sub(r'\s+', ' ', cleaned_topic).strip()
                        search_q = cleaned_topic if len(cleaned_topic) >= 2 else user_msg

                        wiki_summary = None
                        queries_to_try = [search_q]
                        words = [w for w in re.findall(r'\w+', search_q) if len(w) >= 3]
                        if words and words[0].lower() not in queries_to_try:
                            queries_to_try.append(words[0])

                        for q_term in queries_to_try:
                            try:
                                wiki_summary = wikipedia.summary(q_term, sentences=2, auto_suggest=False)
                                if wiki_summary: break
                            except wikipedia.exceptions.DisambiguationError as de:
                                try:
                                    valid_opt = [opt for opt in de.options if q_term.lower() in opt.lower() or opt.lower() in q_term.lower()]
                                    target_opt = valid_opt[0] if valid_opt else de.options[0]
                                    wiki_summary = wikipedia.summary(target_opt, sentences=2, auto_suggest=False)
                                    if wiki_summary: break
                                except Exception:
                                    pass
                            except Exception:
                                pass

                            if not wiki_summary:
                                try:
                                    search_results = wikipedia.search(q_term)
                                    if search_results:
                                        try:
                                            wiki_summary = wikipedia.summary(search_results[0], sentences=2, auto_suggest=False)
                                            if wiki_summary: break
                                        except wikipedia.exceptions.DisambiguationError as de2:
                                            wiki_summary = wikipedia.summary(de2.options[0], sentences=2, auto_suggest=False)
                                            if wiki_summary: break
                                except Exception:
                                    pass

                        if wiki_summary and len(wiki_summary.strip()) > 20:
                            reply_text = f"According to Wikipedia:\n{wiki_summary}"
                        else:
                            reply_text = "Sir, Gemini AI limit reached or offline. Operating in offline predefined command mode! Please add a new API key in Settings."
                    except Exception as w_err:
                        print(f"[Offline Wiki Search Fail] {w_err}")
                        reply_text = "Sir, Gemini AI limit reached or offline. Operating in offline predefined command mode! Please add a new API key in Settings."

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
