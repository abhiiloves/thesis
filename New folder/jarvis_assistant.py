import os
import re
import json
import random
import threading
import queue
import datetime
import webbrowser
import wikipedia
import pyttsx3
import customtkinter as ctk
from google import genai
from google.genai import types

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
            self.speech_queue.put(text)

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
            'who are my friends': ['Your friends are Kushagra Sharma, Vikas Kumar, and Pradeep Sir.'],
            'who is my friend': ['Your friends are Kushagra Sharma, Vikas Kumar, and Pradeep Sir.'],
            'what is my name': ['Your name is Abhii Abhishek Sir!'],
            'my name': ['Your name is Abhii Abhishek Sir!'],
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

        self.selected_model = "gemini-2.5-flash"
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

        # Auto-detect personal / friend fact statements (ONLY when user is TELLING, not asking)
        is_question = "what" in text or "who" in text or "tell" in text or "when" in text
        if not is_question:
            if "my birthday is" in text or "my bday is" in text or "birthday on" in text:
                save_user_knowledge("user_birthday", raw_text)
                resp_str = "Understood Sir, I have saved your birthday to memory."
                self.conversation_context.append({"role": "user", "content": raw_text})
                self.conversation_context.append({"role": "assistant", "content": resp_str})
                return resp_str
            elif "my name is" in text:
                save_user_knowledge("user_name", raw_text)
                resp_str = "Understood Sir, I have saved your name to memory."
                self.conversation_context.append({"role": "user", "content": raw_text})
                self.conversation_context.append({"role": "assistant", "content": resp_str})
                return resp_str
            elif "friend" in text or "friends" in text:
                if "is" in text or "are" in text or "name" in text:
                    save_user_knowledge(f"fact_{datetime.datetime.now().strftime('%H%M%S')}", raw_text)
                    resp_str = "Understood Sir, I have noted and saved your friends' details to memory."
                    self.conversation_context.append({"role": "user", "content": raw_text})
                    self.conversation_context.append({"role": "assistant", "content": resp_str})
                    return resp_str

        # Check predefined responses first
        predefined = self.get_predefined_response(text)
        if predefined:
            self.conversation_context.append({"role": "user", "content": raw_text})
            self.conversation_context.append({"role": "assistant", "content": predefined})
            return predefined

        # Time & Date Queries
        if "time" in text or "current time" in text or "what time" in text:
            now_time = datetime.datetime.now().strftime("%I:%M %p")
            resp_str = f"The current time is {now_time}, Sir."
            self.conversation_context.append({"role": "user", "content": raw_text})
            self.conversation_context.append({"role": "assistant", "content": resp_str})
            return resp_str
        if "date" in text or "today's date" in text or "what date" in text:
            now_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
            resp_str = f"Today's date is {now_date}, Sir."
            self.conversation_context.append({"role": "user", "content": raw_text})
            self.conversation_context.append({"role": "assistant", "content": resp_str})
            return resp_str

        # Web & system triggers
        if "open youtube" in text:
            webbrowser.open("https://www.youtube.com")
            return "Opening YouTube Sir."
        if "open google" in text:
            webbrowser.open("https://www.google.com")
            return "Opening Google Sir."
        if "play music" in text or "play song" in text or "favourite song" in text:
            webbrowser.open("https://www.youtube.com/watch?v=r03GO2AlNUo&t=26s")
            return "Playing your favourite song Sir."
        if "open amazon" in text:
            webbrowser.open("https://www.amazon.com")
            return "Opening Amazon Sir."

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

                prompt_parts = [
                    "You are Jarvis, a sleek, intelligent AI assistant created by Abhii Abhishek. "
                    "Respond concisely and helpfully in 1-3 sentences without markdown headings or bullet points. "
                    + memory_str
                ]
                recent_turns = self.conversation_context[-10:]
                for turn in recent_turns:
                    role_str = "User" if turn["role"] == "user" else "Jarvis"
                    prompt_parts.append(f"{role_str}: {turn['content']}")
                
                prompt_parts.append(f"User: {raw_text}\nJarvis:")

                full_prompt = "\n".join(prompt_parts)

                response = self.gemini_client.models.generate_content(
                    model=self.selected_model,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(max_output_tokens=150, temperature=0.7)
                )
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
            return "Sorry Sir, Gemini AI limit reached or offline. Operating in predefined command mode."
        return "I am not sure how to respond to that Sir."


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
