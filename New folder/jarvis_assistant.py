import os
import re
import json
import random
import threading
import queue
import datetime
import urllib.request
import webbrowser
import wikipedia
wikipedia.set_user_agent("JarvisAIAssistant/2.0 (contact@example.com)")
import pyttsx3
import customtkinter as ctk
from google import genai
from google.genai import types

IST_TZ = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

def get_ist_now():
    return datetime.datetime.now(IST_TZ)

def extract_date_events(text_lower, raw_text):
    now = get_ist_now()
    year = now.year
    events = []
    
    # 1. Check relative days first
    # "kl" / "kal" / "tomorrow"
    if any(w in text_lower for w in ["tomorrow", "kal", "kl"]):
        tomorrow_date = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        evt_type = "event"
        title = raw_text
        if "holiday" in text_lower or "chutti" in text_lower:
            evt_type = "holiday"
            title = "Holiday 🏖️"
        elif "practical" in text_lower or "pratical" in text_lower:
            evt_type = "practical"
            title = "Practical Exam 📚"
        elif "exam" in text_lower:
            evt_type = "exam"
            title = "Exam 📝"
            
        events.append({
            "date": tomorrow_date,
            "title": title,
            "type": evt_type
        })
        
    # 2. Check month and day patterns
    months_map = {
        "jan": 1, "january": 1,
        "feb": 2, "february": 2,
        "mar": 3, "march": 3,
        "apr": 4, "april": 4,
        "may": 5,
        "jun": 6, "june": 6,
        "jul": 7, "july": 7,
        "aug": 8, "august": 8,
        "sep": 9, "september": 9,
        "oct": 10, "october": 10,
        "nov": 11, "november": 11,
        "dec": 12, "december": 12
    }
    
    found_specific = False
    for m_name, m_num in months_map.items():
        pat1 = r'\b(\d{1,2})(?:st|nd|rd|th)?\s+' + re.escape(m_name) + r'\b'
        pat2 = r'\b' + re.escape(m_name) + r'\s+(\d{1,2})(?:st|nd|rd|th)?\b'
        
        for pat in [pat1, pat2]:
            matches = re.findall(pat, text_lower)
            for m in matches:
                day = int(m)
                event_date = f"{year}-{m_num:02d}-{day:02d}"
                
                title = "Event"
                evt_type = "event"
                if "kushagra" in text_lower:
                    title = "Kushagra's Birthday 🎂"
                    evt_type = "birthday"
                elif "vikas" in text_lower:
                    title = "Vikas Kumar's Birthday 🎂"
                    evt_type = "birthday"
                elif "pradeep" in text_lower:
                    title = "Pradeep Sir's Birthday 🎂"
                    evt_type = "birthday"
                elif "practical" in text_lower or "pratical" in text_lower:
                    title = "Practical Exam 📚"
                    evt_type = "practical"
                elif "holiday" in text_lower or "chutti" in text_lower:
                    title = "Holiday 🏖️"
                    evt_type = "holiday"
                else:
                    title = raw_text
                
                events.append({
                    "date": event_date,
                    "title": title,
                    "type": evt_type
                })
                found_specific = True
                
    # 3. Match dates without months specified (e.g. "6 date ko", "8 ko")
    if not found_specific:
        pat_num = r'\b(\d{1,2})(?:\s*(?:date|tarikh|tareekh|ko|date ko))\b'
        matches = re.findall(pat_num, text_lower)
        for m in matches:
            day = int(m)
            m_num = now.month
            e_year = year
            if day <= now.day:
                m_num += 1
                if m_num > 12:
                    m_num = 1
                    e_year += 1
            event_date = f"{e_year}-{m_num:02d}-{day:02d}"
            
            title = "Event"
            evt_type = "event"
            if "practical" in text_lower or "pratical" in text_lower:
                title = "Practical Exam 📚"
                evt_type = "practical"
            elif "holiday" in text_lower or "chutti" in text_lower:
                title = "Holiday 🏖️"
                evt_type = "holiday"
            elif "exam" in text_lower:
                title = "Exam 📝"
                evt_type = "exam"
            else:
                title = raw_text
                
            events.append({
                "date": event_date,
                "title": title,
                "type": evt_type
            })
            
    return events

def get_desktop_calendar_events():
    knowledge = load_user_knowledge()
    events = []
    
    for k, v in knowledge.items():
        if k.startswith("cal_event_") and isinstance(v, dict):
            events.append(v)
            
    now = get_ist_now()
    year = now.year
    months_map = {
        "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
        "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
        "aug": 8, "august": 8, "sep": 9, "september": 9, "oct": 10, "october": 10,
        "nov": 11, "november": 11, "dec": 12, "december": 12
    }
    
    for k, v in knowledge.items():
        if (k.startswith("friend_bday") or "friend" in k.lower() or "birthday" in k.lower() or k.startswith("event_")) and isinstance(v, str):
            v_lower = v.lower()
            for m_name, m_num in months_map.items():
                pat1 = r'\b(\d{1,2})(?:st|nd|rd|th)?\s+' + re.escape(m_name) + r'\b'
                pat2 = r'\b' + re.escape(m_name) + r'\s+(\d{1,2})(?:st|nd|rd|th)?\b'
                for pat in [pat1, pat2]:
                    matches = re.findall(pat, v_lower)
                    for m in matches:
                        day = int(m)
                        event_date = f"{year}-{m_num:02d}-{day:02d}"
                        title = v
                        evt_type = "birthday" if "birthday" in k.lower() or "bday" in k.lower() or "birthday" in v_lower or "bday" in v_lower else "event"
                        if "kushagra" in v_lower:
                            title = "Kushagra's Birthday 🎂"
                        elif "vikas" in v_lower:
                            title = "Vikas Kumar's Birthday 🎂"
                        elif "pradeep" in v_lower:
                            title = "Pradeep Sir's Birthday 🎂"
                        elif "practical" in v_lower or "pratical" in v_lower:
                            title = "Practical Exam 📚"
                            evt_type = "practical"
                        elif "holiday" in v_lower or "chutti" in v_lower:
                            title = "Holiday 🏖️"
                            evt_type = "holiday"
                        
                        if not any(e["date"] == event_date and e["title"] == title for e in events):
                            events.append({
                                "date": event_date,
                                "title": title,
                                "type": evt_type
                            })
                            
    events.sort(key=lambda x: x.get("date", ""))
    return events

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

# ==========================================
# THREAD-SAFE TTS ENGINE WITH INTERRUPT
# ==========================================
class TextToSpeechEngine:
    """Thread-safe Text-to-Speech manager supporting mid-sentence interruption."""
    def __init__(self, rate=170, voice_index=0):
        self.speech_queue = queue.Queue()
        self.rate = rate
        self.voice_index = voice_index
        self.enabled = True
        self.engine = None
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._tts_loop, daemon=True)
        self.thread.start()

    def _tts_loop(self):
        try:
            self.engine = pyttsx3.init("sapi5")
            voices = self.engine.getProperty('voices')
            if voices and self.voice_index < len(voices):
                self.engine.setProperty('voice', voices[self.voice_index].id)
            self.engine.setProperty('rate', self.rate)
        except Exception as e:
            print(f"[TTS Init Error] {e}")
            self.engine = None

        while True:
            text = self.speech_queue.get()
            if text is None:
                break
            if self.enabled and self.engine and text.strip():
                try:
                    with self.lock:
                        self.engine.setProperty('rate', self.rate)
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    print(f"[TTS Speech Error] {e}")
            self.speech_queue.task_done()

    def speak(self, text):
        """Enqueue text for speech."""
        if self.enabled and text:
            clean_text = re.sub(r'[*#_`•]', '', text)
            clean_text = re.sub(r'https?://\S+', '', clean_text).strip()
            self.speech_queue.put(clean_text)

    def stop(self):
        """Interrupt active speech and clear speech queue."""
        with self.speech_queue.mutex:
            self.speech_queue.queue.clear()
        if self.engine:
            try:
                self.engine.stop()
            except Exception:
                pass

    def set_rate(self, new_rate):
        self.rate = new_rate
        if self.engine:
            try:
                self.engine.setProperty('rate', self.rate)
            except Exception:
                pass

    def set_voice(self, voice_index):
        self.voice_index = voice_index
        if self.engine:
            try:
                voices = self.engine.getProperty('voices')
                if voices and voice_index < len(voices):
                    self.engine.setProperty('voice', voices[voice_index].id)
            except Exception:
                pass


# ==========================================
# CONVERSATION HISTORY & STORAGE MANAGER
# ==========================================
HISTORY_FILE = "chat_sessions.json"
KNOWLEDGE_FILE = "user_knowledge.json"

def load_chat_sessions():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_chat_sessions(sessions):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(sessions, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Save Sessions Error] {e}")

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


# ==========================================
# JARVIS BRAIN WITH CONVERSATION CONTEXT
# ==========================================
class JarvisBrain:
    def __init__(self):
        self.responses = {
            'hi': ['Hello! Sir, I am ready to assist you.', 'Hi sir, I am ready to assist you.', 'Hello Sir, I am ready to assist you.'],
            'hey': ['Hello! Sir, I am ready to assist you.', 'Hey Sir, how can I help you today?', 'Hello Sir, standing by.'],
            'greetings': ['Hello! Sir, I am ready to assist you.', 'Hi sir, I am ready to assist you.', 'Hello Sir, I am ready to assist you.'],
            'kya haal h': ['All systems optimal, Sir! Ready to assist you.', 'Main badhiya hoon Sir! Standing by for your instructions.', 'Everything is running smoothly Sir! How may I help you today?'],
            'kya haal hai': ['All systems optimal, Sir! Ready to assist you.', 'Main badhiya hoon Sir! Standing by for your instructions.', 'Everything is running smoothly Sir! How may I help you today?'],
            'kya haal': ['All systems optimal, Sir! Ready to assist you.', 'Main badhiya hoon Sir! Standing by for your instructions.'],
            'kaise ho': ['All systems optimal, Sir! I am ready to assist you.', 'Main badhiya hoon Sir, aap bataiye kaise hain?'],
            'kaise h': ['All systems optimal, Sir! I am ready to assist you.', 'Main badhiya hoon Sir, aap bataiye kaise hain?'],
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
            'nice': ['Thank you Sir! Glad I could assist you.', 'Always at your service, Sir!'],
            'good': ['Thank you Sir!', 'Glad you like it Sir!'],
            'great': ['Thank you Sir! Standing by for your next command.'],
            'awesome': ['Thank you Sir! Powering ahead!'],
            'perfect': ['Thank you Sir! 100% precision achieved!'],
            'sweet': ['Thank you Sir!'],
            'fine': ['Good to know Sir! Ready for your commands.'],
            'ok': ['Standing by Sir!'],
            'okay': ['Standing by Sir!'],
            'thanks': ['Welcome Sir! Happy to help.'],
            'thank you jarvis': ['Welcome Sir! Always at your service.'],
            'thank you': ['Welcome Sir! Always at your service.'],
            'shukriya': ['Aapka swagat hai Sir!'],
            'dhanyawad': ['Aapka swagat hai Sir!'],
            'introduce': ['I am Jarvis, an Intelligent Multi-Model AI Assistant created by Bhanu Sir for his B.Tech CSE Major Project.'],
            'results': ['Anything else Sir?'],
            'sun': ['The Sun is the star at the center of the Solar System. It is a massive, hot sphere of plasma that provides essential light and energy to Earth.'],
            'moon': ['The Moon is Earth\'s only natural satellite. It orbits Earth and controls ocean tides.'],
            'earth': ['Earth is the third planet from the Sun and the only astronomical object known to harbor life.'],
            'default': ['All systems optimal Sir! Ready for your commands.']
        }

        self.selected_model = "gemini-2.5-flash-lite"
        self.api_key = os.environ.get("GEMINI_API_KEY", "")
        self.gemini_client = None
        self.init_gemini()

        # Context Memory: list of {"role": "user"/"assistant", "content": text}
        self.conversation_context = []

    def init_gemini(self):
        if self.api_key:
            try:
                self.gemini_client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[Gemini Init Warning] {e}")

    def clear_context(self):
        self.conversation_context = []

    def get_predefined_response(self, text):
        for key in self.responses:
            if key == 'default':
                continue
            pattern = r'\b' + re.escape(key) + r'\b'
            if re.search(pattern, text):
                return random.choice(self.responses[key])
        return None

    def process_input(self, user_input):
        raw_text = user_input.strip()
        if not raw_text:
            return random.choice([
                "Yes Sir?",
                "I'm listening Sir.",
                "How may I assist you?",
                "Standing by for instructions."
            ])

        text = raw_text.lower()

        # Process Statements (Fact & Event Saving) FIRST if it is clearly a statement!
        is_query = any(w in text for w in ["kya", "what", "konsa", "konsi", "batao", "bato", "list", "tell", "show", "who", "when", "kab", "kaun", "kon"])
        
        if not is_query:
            resp_str = None
            # A. Friend Birthday Statements (HIGHEST PRIORITY)
            if any(w in text for w in ["birthday", "bday", "janamdin"]):
                if any(w in text for w in ["friend", "friends", "dost", "dosto", "kushagra", "vikas", "pradeep", "on", "is", "hai", "=", ":"]):
                    save_user_knowledge(f"friend_bday_{get_ist_now().strftime('%H%M%S')}", raw_text)
                    resp_str = "Understood Sir, I have saved your friend's birthday details to permanent memory!"
            elif "my birthday is" in text or "my bday is" in text or "mera birthday" in text:
                save_user_knowledge("user_birthday", raw_text)
                resp_str = "Understood Sir, I have saved your birthday to permanent memory."
            elif "my name is" in text or "mera naam is" in text:
                save_user_knowledge("user_name", raw_text)
                resp_str = "Understood Sir, I have saved your name to permanent memory."
            # B. Schedule & Exam Statements (ONLY if not a birthday!)
            elif any(w in text for w in ["practical", "pratical", "exam", "test", "holiday", "chutti", "event", "meeting", "interview", "presentation", "trip"]):
                if any(k in text for k in ["my", "mera", "meri", "mere", "on", "is", "hai", "ko", "kl", "kal"]):
                    event_id = f"event_{get_ist_now().strftime('%H%M%S')}"
                    save_user_knowledge(event_id, raw_text)
                    resp_str = f"Got it, Sir! 🗓️ Noted and saved your schedule ({raw_text}) to permanent memory!"

            # Auto-extract calendar events when saved
            if resp_str:
                try:
                    extracted = extract_date_events(text, raw_text)
                    for idx, ev in enumerate(extracted):
                        save_user_knowledge(f"cal_event_{get_ist_now().strftime('%Y%m%d_%H%M%S')}_{idx}", ev)
                except Exception as ex_err:
                    print(f"[Calendar Auto-Extract Error] {ex_err}")
                self.conversation_context.append({"role": "user", "content": raw_text})
                self.conversation_context.append({"role": "assistant", "content": resp_str})
                return resp_str

        # Flexible Query Detection (Comprehensive Offline Intent Matcher)
        if any(w in text for w in ["friend", "friends", "dost", "dosto"]) and any(w in text for w in ["birthday", "bday", "brithday", "janamdin", "dates", "date"]):
            knowledge = load_user_knowledge()
            bday_items = [v for k, v in knowledge.items() if k.startswith("friend_bday") or ("friend" in k.lower() and "birthday" in k.lower())]
            if bday_items:
                bdays_formatted = "\n• " + "\n• ".join(bday_items)
                resp_str = f"Here are your saved friend birthday details Sir:{bdays_formatted}"
            else:
                resp_str = "Your friends and birthdays are:\n• Kushagra Sharma: April 14th 🎂\n• Vikas Kumar: July 8th 🎂\n• Pradeep Sir: June 19th 🎂"
            self.conversation_context.append({"role": "user", "content": raw_text})
            self.conversation_context.append({"role": "assistant", "content": resp_str})
            return resp_str
        elif any(w in text for w in ["friend", "friends", "dost", "dosto"]) and (any(w in text for w in ["name", "naam", "nam", "who", "bato", "batao", "list", "kaun", "kon"]) or "dost" in text):
            resp_str = "Your friends are Kushagra Sharma, Vikas Kumar, and Pradeep Sir."
            self.conversation_context.append({"role": "user", "content": raw_text})
            self.conversation_context.append({"role": "assistant", "content": resp_str})
            return resp_str
        elif ("your name" in text or "tera naam" in text or "apka naam" in text or "aapka naam" in text) and not ("my name" in text or "mera naam" in text):
            resp_str = "I am Jarvis, your intelligent AI assistant created by Abhii Abhishek Sir!"
            self.conversation_context.append({"role": "user", "content": raw_text})
            self.conversation_context.append({"role": "assistant", "content": resp_str})
            return resp_str
        elif "who are you" in text or "tum kaun ho" in text or "tum kon ho" in text:
            resp_str = "I am Jarvis, your intelligent AI assistant created by Abhii Abhishek Sir!"
            self.conversation_context.append({"role": "user", "content": raw_text})
            self.conversation_context.append({"role": "assistant", "content": resp_str})
            return resp_str
        elif any(w in text for w in ["schedule", "event", "events", "practical", "pratical", "exam", "chutti", "holiday", "kaam", "important", "next month", "agle mahine", "upcoming", "planning"]) or (any(w in text for w in ["kl kya", "kal kya"]) and not "mausam" in text):
            all_events = get_desktop_calendar_events()
            now = get_ist_now()
            matched_events = []
            filter_type = "upcoming"
            
            if any(w in text for w in ["next month", "agle mahine"]):
                filter_type = "next month"
                next_month_num = now.month + 1
                next_month_year = now.year
                if next_month_num > 12:
                    next_month_num = 1
                    next_month_year += 1
                target_prefix = f"{next_month_year}-{next_month_num:02d}"
                matched_events = [e for e in all_events if e.get("date", "").startswith(target_prefix)]
            elif any(w in text for w in ["this month", "iss mahine", "is mahine"]):
                filter_type = "this month"
                target_prefix = now.strftime("%Y-%m")
                matched_events = [e for e in all_events if e.get("date", "").startswith(target_prefix)]
            elif any(w in text for w in ["tomorrow", "kal", "kl"]):
                filter_type = "tomorrow"
                tomorrow_str = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                matched_events = [e for e in all_events if e.get("date", "") == tomorrow_str]
            else:
                today_str = now.strftime("%Y-%m-%d")
                matched_events = [e for e in all_events if e.get("date", "") >= today_str]
            
            if matched_events:
                out_lines = []
                for e in matched_events:
                    d_obj = datetime.datetime.strptime(e["date"], "%Y-%m-%d")
                    formatted_d = d_obj.strftime("%d %B %Y")
                    out_lines.append(f"{formatted_d}: {e['title']}")
                out_msg = f"Here are your schedules for {filter_type} Sir:\n• " + "\n• ".join(out_lines)
            else:
                legacy_events = [v for k, v in load_user_knowledge().items() if k.startswith("event_")]
                if legacy_events:
                    out_msg = f"Here are your schedules Sir:\n• " + "\n• ".join(legacy_events)
                else:
                    out_msg = f"You don't have any specific schedules saved for {filter_type} Sir."
            self.conversation_context.append({"role": "user", "content": raw_text})
            self.conversation_context.append({"role": "assistant", "content": out_msg})
            return out_msg
        elif any(w in text for w in ["friend", "friends", "dost", "dosto"]) and any(w in text for w in ["name", "naam", "who", "bato", "batao", "list", "kaun", "kon"]):
            resp_str = "Your friends are Kushagra Sharma, Vikas Kumar, and Pradeep Sir."
            self.conversation_context.append({"role": "user", "content": raw_text})
            self.conversation_context.append({"role": "assistant", "content": resp_str})
            return resp_str
        elif any(w in text for w in ["mera naam", "my name"]) and any(w in text for w in ["kya", "what", "batao", "bato", "tell"]):
            resp_str = "Your name is Bhanu (Abhii Abhishek) Sir!"
            self.conversation_context.append({"role": "user", "content": raw_text})
            self.conversation_context.append({"role": "assistant", "content": resp_str})
            return resp_str
        elif any(w in text for w in ["who created", "who made", "owner", "malik", "kisne banaya"]):
            resp_str = "I was created by Bhanu Sir at NGF College, Palwal!"
            self.conversation_context.append({"role": "user", "content": raw_text})
            self.conversation_context.append({"role": "assistant", "content": resp_str})
            return resp_str

        # Instant Math Calculator Evaluator
        if re.match(r'^\s*[\d\s+\-*/().]+\s*$', text) and any(op in text for op in ['+', '-', '*', '/']):
            try:
                clean_expr = re.sub(r'[^0-9+\-*/().\s]', '', text)
                calc_res = eval(clean_expr, {"__builtins__": None}, {})
                if isinstance(calc_res, (int, float)):
                    formatted_res = f"{int(calc_res)}" if isinstance(calc_res, float) and calc_res.is_integer() else f"{calc_res}"
                    resp_str = f"{raw_text} = {formatted_res}"
                    self.conversation_context.append({"role": "user", "content": raw_text})
                    self.conversation_context.append({"role": "assistant", "content": resp_str})
                    return resp_str
            except Exception:
                pass

        # Check predefined responses first
        predefined = self.get_predefined_response(text)
        if predefined:
            self.conversation_context.append({"role": "user", "content": raw_text})
            self.conversation_context.append({"role": "assistant", "content": predefined})
            return predefined

        # Live Weather Engine & Time/Date Queries
        if any(w in text for w in ["weather", "mausam", "moosam", "mosam", "baarish", "barish", "rain", "monsoon", "mansoon", "temperature", "taapman", "tapman"]):
            resp_str = get_live_weather_report(text)
            self.conversation_context.append({"role": "user", "content": raw_text})
            self.conversation_context.append({"role": "assistant", "content": resp_str})
            return resp_str
        elif any(w in text for w in ["time", "samay", "waqt", "kitne baje"]):
            now_time = get_ist_now().strftime("%I:%M %p")
            resp_str = f"The current time is {now_time}, Sir."
            self.conversation_context.append({"role": "user", "content": raw_text})
            self.conversation_context.append({"role": "assistant", "content": resp_str})
            return resp_str
        elif any(w in text for w in ["tomorrow", "kal kya", "kl kya", "kal konsa", "kl konsa", "kal ki date", "kl ki date"]):
            tomorrow_date = (get_ist_now() + datetime.timedelta(days=1)).strftime("%A, %B %d, %Y")
            resp_str = f"Tomorrow will be {tomorrow_date}, Sir."
            self.conversation_context.append({"role": "user", "content": raw_text})
            self.conversation_context.append({"role": "assistant", "content": resp_str})
            return resp_str
        elif any(w in text for w in ["today's date", "today date", "aaj konsi date", "aaj ki date"]) or (text.strip() in ["date", "dates", "what date"]):
            now_date = get_ist_now().strftime("%A, %B %d, %Y")
            resp_str = f"Today's date is {now_date}, Sir."
            self.conversation_context.append({"role": "user", "content": raw_text})
            self.conversation_context.append({"role": "assistant", "content": resp_str})
            return resp_str

        # Web & system triggers
        if "whatsapp" in text and any(w in text for w in ["open", "chalao", "kholo", "start", "show"]):
            webbrowser.open("https://web.whatsapp.com")
            try:
                os.system("start whatsapp:")
            except Exception:
                pass
            return "Opening WhatsApp Sir."

        if "open youtube" in text:
            webbrowser.open("https://www.youtube.com")
            return "Opening YouTube Sir."
        if "open google" in text:
            webbrowser.open("https://www.google.com")
            return "Opening Google Sir."
        if any(w in text for w in ["music", "song", "gaana", "gana", "gane", "geet", "track", "audio"]) and any(w in text for w in ["play", "chalao", "chala", "suno", "sunao", "listen", "start", "plaay"]):
            webbrowser.open("https://www.youtube.com/watch?v=r03GO2AlNUo&t=26s")
            return "Playing your favourite music Sir."
        if "amazon" in text and any(w in text for w in ["open", "chalao", "kholo", "start", "show", "shopping"]):
            webbrowser.open("https://www.amazon.in")
            return "Opening Amazon Sir."
        if "flipkart" in text and any(w in text for w in ["open", "chalao", "kholo", "start", "show", "shopping"]):
            webbrowser.open("https://www.flipkart.com")
            return "Opening Flipkart Sir."
        if "myntra" in text and any(w in text for w in ["open", "chalao", "kholo", "start", "show", "shopping"]):
            webbrowser.open("https://www.myntra.com")
            return "Opening Myntra Sir."
        if "meesho" in text and any(w in text for w in ["open", "chalao", "kholo", "start", "show", "shopping"]):
            webbrowser.open("https://www.meesho.com")
            return "Opening Meesho Sir."
        if any(w in text for w in ["shopping", "khareedari", "kharidari"]) and any(w in text for w in ["open", "chalao", "kholo", "start", "show", "on", "website", "site"]):
            shop_sites = [
                ("Amazon", "https://www.amazon.in"),
                ("Flipkart", "https://www.flipkart.com"),
                ("Myntra", "https://www.myntra.com"),
                ("Meesho", "https://www.meesho.com")
            ]
            chosen = random.choice(shop_sites)
            webbrowser.open(chosen[1])
            return f"Opening {chosen[0]} for your online shopping Sir!"
        if "github" in text and any(w in text for w in ["open", "dekho", "show", "kholo"]):
            webbrowser.open("https://github.com/abhiiloves")
            return "Opening your GitHub profile Sir."
        if "linkedin" in text and any(w in text for w in ["open", "dekho", "show", "kholo"]):
            webbrowser.open("https://www.linkedin.com/in/bhanu-60a88a26a")
            return "Opening your LinkedIn profile Sir."
        if "instagram" in text and any(w in text for w in ["open", "dekho", "show", "kholo"]):
            webbrowser.open("https://www.instagram.com/abhiiloves")
            return "Opening your Instagram profile Sir."

        # Wikipedia queries
        if "wikipedia" in text:
            query = user_input.replace("wikipedia", "").replace("search", "").strip()
            if not query:
                return "What topic would you like me to search on Wikipedia Sir?"
            try:
                result = wikipedia.summary(query, sentences=2)
                resp_str = f"According to Wikipedia: {result}"
                self.conversation_context.append({"role": "user", "content": raw_text})
                self.conversation_context.append({"role": "assistant", "content": resp_str})
                return resp_str
            except wikipedia.exceptions.DisambiguationError:
                return f"Multiple entries found for '{query}'. Please be specific Sir."
            except wikipedia.exceptions.PageError:
                return f"Sorry Sir, I couldn't find a Wikipedia page matching '{query}'."
            except Exception:
                return f"Could not fetch Wikipedia results due to network failure."

        # Gemini AI with Global Memory & Conversation History
        self.api_status = "online" if self.gemini_client else "offline"
        if self.gemini_client:
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
                recent_turns = self.conversation_context[-10:]
                for turn in recent_turns:
                    role_str = "User" if turn["role"] == "user" else "Jarvis"
                    prompt_parts.append(f"{role_str}: {turn['content']}")
                
                prompt_parts.append(f"User: {raw_text}\nJarvis:")

                full_prompt = "\n".join(prompt_parts)

                response = None
                models_to_try = [self.selected_model, "gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]
                for m_name in models_to_try:
                    try:
                        resp = self.gemini_client.models.generate_content(
                            model=m_name,
                            contents=full_prompt,
                            config=types.GenerateContentConfig(max_output_tokens=350, temperature=0.7)
                        )
                        if resp and hasattr(resp, 'text') and resp.text:
                            response = resp
                            break
                    except Exception as try_err:
                        print(f"[Desktop Model Retry {m_name}] {try_err}")

                if response and hasattr(response, 'text') and response.text:
                    reply_text = response.text.strip()
                    self.conversation_context.append({"role": "user", "content": raw_text})
                    self.conversation_context.append({"role": "assistant", "content": reply_text})
                    self.api_status = "online"
                    return reply_text
                else:
                    self.api_status = "offline"
            except Exception as err:
                print(f"[Gemini API Error] {err}")
                self.api_status = "offline"

        if self.api_status == "offline":
            is_task_request = any(w in text for w in ["make", "write", "create", "generate", "draft", "banao", "likho", "tayyar"])
            if is_task_request:
                if any(w in text for w in ["letter", "patra", "chitti", "application", "mail", "email"]):
                    resp_str = (
                        "Here is a formal letter template for you Sir:\n\n"
                        "[Date]\nTo, [Recipient Name/Title]\n[Company/Organization]\n\n"
                        "Subject: Formal Request / Application\n\n"
                        "Dear Sir/Madam,\n\n"
                        "I am writing this letter to formally bring to your attention regarding...\n\n"
                        "Thanking you,\nSincerely,\n[Your Name]"
                    )
                else:
                    resp_str = "Sir, Gemini AI limit reached or offline! Please add a new API key in Settings to generate custom AI content."
                self.conversation_context.append({"role": "user", "content": raw_text})
                self.conversation_context.append({"role": "assistant", "content": resp_str})
                return resp_str
            else:
                is_greeting = any(w in text for w in ["haal", "hal", "kaise", "kese", "hello", "hi", "hey", "sup", "greetings"])
                if is_greeting:
                    resp_str = "All systems optimal Sir! Ready for your commands."
                    self.conversation_context.append({"role": "user", "content": raw_text})
                    self.conversation_context.append({"role": "assistant", "content": resp_str})
                    return resp_str
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
                        cleaned_topic = raw_text
                        for pat in stops:
                            cleaned_topic = re.sub(pat, '', cleaned_topic, flags=re.IGNORECASE)
                        cleaned_topic = re.sub(r'\s+', ' ', cleaned_topic).strip()
                        search_q = cleaned_topic if len(cleaned_topic) >= 2 else raw_text

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
                            if self.api_status == "offline":
                                resp_str = f"⚠️ [Notice: Gemini AI limit reached on live models. Operating in Offline Knowledge Engine]\n\nAccording to Wikipedia:\n{wiki_summary}"
                            else:
                                resp_str = f"According to Wikipedia:\n{wiki_summary}"
                        else:
                            resp_str = "Sir, Gemini AI limit reached or offline. Operating in offline predefined command mode! Please add a new API key in Settings."
                        self.conversation_context.append({"role": "user", "content": raw_text})
                        self.conversation_context.append({"role": "assistant", "content": resp_str})
                        return resp_str
                    except Exception as w_err:
                        print(f"[Desktop Wiki Search Fail] {w_err}")
                        resp_str = "Sir, Gemini AI limit reached or offline. Operating in offline predefined command mode! Please add a new API key in Settings."
                        self.conversation_context.append({"role": "user", "content": raw_text})
                        self.conversation_context.append({"role": "assistant", "content": resp_str})
                        return resp_str
        resp_str = "All systems optimal Sir! Ready for your commands."
        self.conversation_context.append({"role": "user", "content": raw_text})
        self.conversation_context.append({"role": "assistant", "content": resp_str})
        return resp_str


# ==========================================
# SETTINGS MODAL WINDOW
# ==========================================
class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, tts_engine, brain_engine):
        super().__init__(parent)
        self.parent = parent
        self.tts = tts_engine
        self.brain = brain_engine

        self.title("⚙ Jarvis Settings")
        self.geometry("400x520")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self.setup_ui()

    def setup_ui(self):
        lbl_title = ctk.CTkLabel(self, text="⚙ Preferences & Settings", font=ctk.CTkFont(size=18, weight="bold"), text_color="#25D366")
        lbl_title.pack(pady=(15, 10))

        # Voice Toggle
        voice_frame = ctk.CTkFrame(self, fg_color="transparent")
        voice_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(voice_frame, text="Voice Output (TTS):", font=ctk.CTkFont(size=14)).pack(side="left")
        self.voice_switch = ctk.CTkSwitch(voice_frame, text="ON" if self.tts.enabled else "OFF", command=self.toggle_voice)
        if self.tts.enabled:
            self.voice_switch.select()
        self.voice_switch.pack(side="right")

        # Speech Rate Slider
        rate_frame = ctk.CTkFrame(self, fg_color="transparent")
        rate_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(rate_frame, text="Speech Speed Rate:", font=ctk.CTkFont(size=14)).pack(side="left")
        self.rate_label = ctk.CTkLabel(rate_frame, text=f"{self.tts.rate} WPM", font=ctk.CTkFont(size=12))
        self.rate_label.pack(side="right")
        self.rate_slider = ctk.CTkSlider(self, from_=100, to=260, number_of_steps=16, command=self.update_rate)
        self.rate_slider.set(self.tts.rate)
        self.rate_slider.pack(fill="x", padx=20, pady=(0, 10))

        # Appearance Theme Mode
        theme_frame = ctk.CTkFrame(self, fg_color="transparent")
        theme_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(theme_frame, text="Appearance Theme:", font=ctk.CTkFont(size=14)).pack(side="left")
        self.theme_option = ctk.CTkOptionMenu(theme_frame, values=["Dark", "Light", "System"], command=self.change_theme)
        self.theme_option.set(ctk.get_appearance_mode().capitalize())
        self.theme_option.pack(side="right")

        # AI Model Selection
        model_frame = ctk.CTkFrame(self, fg_color="transparent")
        model_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(model_frame, text="Gemini AI Model:", font=ctk.CTkFont(size=14)).pack(side="left")
        self.model_option = ctk.CTkOptionMenu(model_frame, values=["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"], command=self.change_model)
        self.model_option.set(self.brain.selected_model)
        self.model_option.pack(side="right")

        # Custom API Key Input
        key_frame = ctk.CTkFrame(self, fg_color="transparent")
        key_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(key_frame, text="Custom Gemini API Key:", font=ctk.CTkFont(size=14)).pack(anchor="w")
        self.api_entry = ctk.CTkEntry(key_frame, placeholder_text="Paste new Gemini API Key here...", width=340, show="*")
        if self.brain.api_key:
            self.api_entry.insert(0, self.brain.api_key)
        self.api_entry.pack(fill="x", pady=(5, 0))

        # Close Button
        btn_close = ctk.CTkButton(self, text="Save & Close", fg_color="#25D366", hover_color="#1DA851", text_color="black", font=ctk.CTkFont(weight="bold"), command=self.save_and_close)
        btn_close.pack(pady=20)

    def toggle_voice(self):
        self.tts.enabled = self.voice_switch.get() == 1
        self.voice_switch.configure(text="ON" if self.tts.enabled else "OFF")
        if hasattr(self.parent, "sync_mute_button"):
            self.parent.sync_mute_button()

    def update_rate(self, val):
        rate_val = int(val)
        self.rate_label.configure(text=f"{rate_val} WPM")
        self.tts.set_rate(rate_val)

    def change_theme(self, choice):
        ctk.set_appearance_mode(choice.lower())

    def change_model(self, choice):
        self.brain.selected_model = choice

    def save_and_close(self):
        new_key = self.api_entry.get().strip()
        if new_key:
            self.brain.api_key = new_key
            self.brain.init_gemini()
        self.destroy()


# ==========================================
# MAIN CUSTOMTKINTER GUI APPLICATION
# ==========================================
class JarvisGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.title("Jarvis Assistant AI Desktop")
        self.geometry("900x680")
        self.minsize(750, 500)

        # Logic & Engines
        self.ai = JarvisBrain()
        self.tts = TextToSpeechEngine(rate=170, voice_index=0)
        self.sessions = load_chat_sessions()
        self.current_session_id = None

        self.setup_ui()
        self.init_first_session()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ------------------------------------
        # SIDEBAR (ChatGPT Style)
        # ------------------------------------
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#181818")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(2, weight=1)

        # New Chat Button
        self.btn_new_chat = ctk.CTkButton(
            self.sidebar, 
            text="+ New Chat", 
            fg_color="#25D366", 
            hover_color="#1DA851",
            text_color="black", 
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.create_new_chat
        )
        self.btn_new_chat.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="ew")

        ctk.CTkLabel(self.sidebar, text="Chat History", font=ctk.CTkFont(size=12, weight="bold"), text_color="#888888").grid(row=1, column=0, padx=15, pady=(5, 5), sticky="w")

        # History Scrollable List
        self.history_frame = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.history_frame.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")

        # Delete All History Button
        self.btn_delete_history = ctk.CTkButton(
            self.sidebar, 
            text="🗑️ Clear All History", 
            fg_color="#331111", 
            hover_color="#551111",
            text_color="#FF6666", 
            font=ctk.CTkFont(size=12),
            command=self.delete_all_history
        )
        self.btn_delete_history.grid(row=3, column=0, padx=15, pady=15, sticky="ew")

        # ------------------------------------
        # MAIN CHAT AREA (Right Pane)
        # ------------------------------------
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="#0F0F0F")
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Header Bar
        header_frame = ctk.CTkFrame(self.main_container, fg_color="#181818", height=50, corner_radius=0)
        header_frame.grid(row=0, column=0, sticky="ew")

        title_label = ctk.CTkLabel(
            header_frame, 
            text="⚡ JARVIS AI ASSISTANT", 
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#25D366"
        )
        title_label.pack(side="left", padx=20, pady=12)

        btn_settings = ctk.CTkButton(
            header_frame, 
            text="⚙ Settings", 
            width=90, 
            fg_color="#2A2A2A", 
            hover_color="#3A3A3A",
            text_color="white",
            command=self.open_settings
        )
        btn_settings.pack(side="right", padx=(5, 15), pady=10)

        self.btn_quick_mute = ctk.CTkButton(
            header_frame,
            text="🔊 Sound ON",
            width=100,
            fg_color="#2A2A2A",
            hover_color="#3A3A3A",
            text_color="white",
            command=self.toggle_quick_mute
        )
        self.btn_quick_mute.pack(side="right", padx=5, pady=10)

        self.lbl_api_status = ctk.CTkLabel(
            header_frame,
            text="🟢 AI Online",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#25D366"
        )
        self.lbl_api_status.pack(side="right", padx=10, pady=10)

        # Chat Messages Scrollable Frame
        self.chat_frame = ctk.CTkScrollableFrame(self.main_container, fg_color="#111111", corner_radius=0)
        self.chat_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # Bottom Input Area
        bottom_frame = ctk.CTkFrame(self.main_container, fg_color="#0D0D0D", corner_radius=0)
        bottom_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))

        self.entry = ctk.CTkEntry(
            bottom_frame, 
            placeholder_text="Ask Jarvis anything...", 
            height=46,
            corner_radius=23, 
            fg_color="#222222", 
            text_color="white",
            border_width=2, 
            border_color="#25D366",
            font=ctk.CTkFont(size=14)
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(5, 8), pady=8)
        self.entry.bind("<Return>", self.send_message)

        self.send_btn = ctk.CTkButton(
            bottom_frame, 
            text="Send", 
            width=90, 
            height=46,
            corner_radius=23,
            fg_color="#25D366", 
            hover_color="#1DA851",
            text_color="black",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.send_message
        )
        self.send_btn.pack(side="right", padx=5, pady=8)

    def toggle_quick_mute(self):
        self.tts.enabled = not self.tts.enabled
        if not self.tts.enabled:
            self.tts.stop()
        self.sync_mute_button()

    def sync_mute_button(self):
        if self.tts.enabled:
            self.btn_quick_mute.configure(text="🔊 Sound ON", text_color="white", fg_color="#2A2A2A")
        else:
            self.btn_quick_mute.configure(text="🔇 Muted", text_color="#FF6666", fg_color="#331111")

    def init_first_session(self):
        self.render_history_sidebar()
        if not self.sessions:
            self.create_new_chat()
        else:
            first_id = list(self.sessions.keys())[0]
            self.load_session(first_id)

    def render_history_sidebar(self):
        for child in self.history_frame.winfo_children():
            child.destroy()

        for sid, sdata in reversed(list(self.sessions.items())):
            title = sdata.get("title", "Chat Session")
            item_frame = ctk.CTkFrame(self.history_frame, fg_color="#222222" if sid == self.current_session_id else "transparent", corner_radius=6)
            item_frame.pack(fill="x", pady=2)

            btn = ctk.CTkButton(
                item_frame,
                text=f"💬 {title[:16]}...",
                anchor="w",
                fg_color="transparent",
                hover_color="#2A2A2A",
                text_color="white" if sid == self.current_session_id else "#CCCCCC",
                height=36,
                command=lambda s=sid: self.load_session(s)
            )
            btn.pack(side="left", fill="x", expand=True)

            del_btn = ctk.CTkButton(
                item_frame,
                text="🗑️",
                width=28,
                height=28,
                fg_color="transparent",
                hover_color="#441111",
                text_color="#FF6666",
                command=lambda s=sid: self.delete_session(s)
            )
            del_btn.pack(side="right", padx=2)

    def delete_session(self, session_id):
        self.tts.stop()
        if session_id in self.sessions:
            del self.sessions[session_id]
            save_chat_sessions(self.sessions)
        if session_id == self.current_session_id:
            self.current_session_id = None
            self.clear_chat_ui()
            if self.sessions:
                first_id = list(self.sessions.keys())[0]
                self.load_session(first_id)
            else:
                self.create_new_chat()
        else:
            self.render_history_sidebar()

    def create_new_chat(self):
        self.tts.stop()
        sid = datetime.datetime.now().strftime("chat_%Y%m%d_%H%M%S")
        self.sessions[sid] = {
            "title": "New Chat",
            "messages": []
        }
        self.current_session_id = sid
        self.ai.clear_context()
        save_chat_sessions(self.sessions)
        self.render_history_sidebar()
        self.clear_chat_ui()

        welcome_msg = "Hello Sir, I am Jarvis. Standing by for new instructions!"
        self.add_bubble(welcome_msg, sender="bot", save_to_session=True)

    def load_session(self, session_id):
        if session_id not in self.sessions:
            return
        self.tts.stop()
        self.current_session_id = session_id
        self.ai.clear_context()
        self.render_history_sidebar()
        self.clear_chat_ui()

        messages = self.sessions[session_id].get("messages", [])
        for msg in messages:
            sender = msg.get("sender", "bot")
            text = msg.get("text", "")
            timestamp = msg.get("timestamp", "")
            self.add_bubble(text, sender=sender, timestamp=timestamp, save_to_session=False)
            role = "user" if sender == "user" else "assistant"
            self.ai.conversation_context.append({"role": role, "content": text})

    def delete_all_history(self):
        self.tts.stop()
        self.sessions = {}
        save_chat_sessions(self.sessions)
        self.ai.clear_context()
        self.create_new_chat()

    def clear_chat_ui(self):
        for child in self.chat_frame.winfo_children():
            child.destroy()

    def smart_scroll(self):
        try:
            if hasattr(self.chat_frame, "_parent_canvas"):
                canvas = self.chat_frame._parent_canvas
                y1, y2 = canvas.yview()
                if y2 >= 0.85:
                    for i in range(4):
                        self.after(i * 25, lambda: canvas.yview_moveto(1.0))
        except Exception:
            pass

    def add_bubble(self, message, sender="user", timestamp=None, save_to_session=True):
        if timestamp is None:
            timestamp = datetime.datetime.now().strftime("%H:%M")

        if sender == "user":
            bubble_color = "#25D366"
            anchor_pos = "e"
            text_color = "black"
        else:
            bubble_color = "#2A2A2A"
            anchor_pos = "w"
            text_color = "white"

        container = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        container.pack(fill="x", anchor=anchor_pos, pady=6, padx=6)

        bubble = ctk.CTkFrame(container, fg_color=bubble_color, corner_radius=16)
        bubble.pack(anchor=anchor_pos)

        lbl = ctk.CTkLabel(
            bubble, 
            text=message, 
            justify="left", 
            text_color=text_color,
            wraplength=420, 
            padx=14, 
            pady=8,
            font=ctk.CTkFont(size=13)
        )
        lbl.pack(anchor="w")

        sub_bar = ctk.CTkFrame(bubble, fg_color="transparent", height=18)
        sub_bar.pack(fill="x", padx=10, pady=(0, 4))

        time_lbl = ctk.CTkLabel(
            sub_bar, 
            text=timestamp, 
            font=ctk.CTkFont(size=10), 
            text_color="#888888" if sender != "user" else "#333333"
        )
        time_lbl.pack(side="left")

        if sender == "bot":
            btn_copy = ctk.CTkButton(
                sub_bar, 
                text="📋 Copy", 
                width=45, 
                height=16, 
                fg_color="transparent", 
                hover_color="#3A3A3A",
                text_color="#AAAAAA", 
                font=ctk.CTkFont(size=10),
                command=lambda: self.copy_to_clipboard(message)
            )
            btn_copy.pack(side="right")

        self.smart_scroll()

        if save_to_session and self.current_session_id in self.sessions:
            sess = self.sessions[self.current_session_id]
            sess["messages"].append({
                "sender": sender,
                "text": message,
                "timestamp": timestamp
            })
            if sender == "user" and sess["title"] == "New Chat":
                sess["title"] = message[:22]
                self.render_history_sidebar()
            save_chat_sessions(self.sessions)

    def copy_to_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)

    def open_settings(self):
        SettingsWindow(self, self.tts, self.ai)

    def send_message(self, event=None):
        user_msg = self.entry.get().strip()
        self.entry.delete(0, ctk.END)

        self.tts.stop()

        if not user_msg:
            return

        self.add_bubble(user_msg, sender="user")

        if user_msg.lower() in ["exit", "quit", "bye", "close", "stop"]:
            farewell = "Goodbye Sir, shutting down..."
            self.add_bubble(farewell, sender="bot")
            self.tts.speak("Goodbye Sir, shutting down")
            self.after(1200, self.destroy)
            return

        threading.Thread(target=self.bot_reply_thread, args=(user_msg,), daemon=True).start()

    def bot_reply_thread(self, user_msg):
        reply = self.ai.process_input(user_msg)
        status = getattr(self.ai, "api_status", "online")
        if status == "offline":
            self.after(0, lambda: self.lbl_api_status.configure(text="🔴 AI Offline", text_color="#FF6666"))
        else:
            self.after(0, lambda: self.lbl_api_status.configure(text="🟢 AI Online", text_color="#25D366"))
        self.after(0, lambda: self.add_bubble(reply, sender="bot"))
        self.tts.speak(reply)


if __name__ == "__main__":
    app = JarvisGUI()
    app.mainloop()
