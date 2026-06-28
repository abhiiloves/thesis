import random
import pyttsx3
import webbrowser
import datetime
import wikipedia
from google import genai
import os
import customtkinter as ctk
import threading
import queue

# ==========================================
# 1. Thread-Safe Speech Handler (pyttsx3)
# ==========================================
class TextToSpeechEngine:
    """
    Dedicated background thread for text-to-speech execution.
    Prevents SAPI5 COM concurrency crashes and audio overlap issues.
    """
    def __init__(self):
        self.speech_queue = queue.Queue()
        self.thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.thread.start()

    def _speech_worker(self):
        try:
            engine = pyttsx3.init("sapi5")
            voices = engine.getProperty('voices')
            if voices:
                engine.setProperty('voice', voices[0].id)
            engine.setProperty('rate', 170)
        except Exception as e:
            print(f"[TTS Initialization Warning] Could not initialize pyttsx3: {e}")
            engine = None

        while True:
            text = self.speech_queue.get()
            if text is None:
                break
            if engine:
                try:
                    engine.say(text)
                    engine.runAndWait()
                except Exception as err:
                    print(f"[TTS Speech Error] {err}")
            self.speech_queue.task_done()

    def speak(self, text):
        if text and isinstance(text, str):
            self.speech_queue.put(text)

# Instantiate global TTS engine worker
tts = TextToSpeechEngine()

# ==========================================
# 2. Utility & Persistence Functions
# ==========================================
def save_chat_history(user_text, bot_reply):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open("chat_history.txt", "a", encoding="utf-8") as file:
            file.write(f"[{timestamp}] USER: {user_text}\n")
            file.write(f"[{timestamp}] BOT : {bot_reply}\n\n")
    except Exception as e:
        print(f"Error saving chat history: {e}")

def save_knowledge(key, value):
    try:
        with open("knowledge.txt", "a", encoding="utf-8") as f:
            f.write(f"{key}:{value}\n")
    except Exception as e:
        print(f"Error saving knowledge: {e}")

# ==========================================
# 3. Gemini Client & Jarvis Brain
# ==========================================
# Load API key from environment variable safely (prevents leaking keys in plaintext)
api_key = os.environ.get("GEMINI_API_KEY", "")
client = None
if api_key:
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"[Gemini Client Warning] Initialization failed: {e}")

class JarvisBrain:
    def __init__(self):
        self.responses = {
            'hi': ['Hello! Sir, I am ready to assist you.', 'Hi sir, I am ready to assist you.', 'Hello Sir, I am ready to assist you.'],
            'greetings': ['Hello! Sir, I am ready to assist you.', 'Hi sir, I am ready to assist you.', 'Hello Sir, I am ready to assist you.'],
            'my friends name': ['Vikas Kumar, Kushagra', 'Pradeep'],
            'your owner': ['Abhii Abhishek', 'Bhanu Pratap Singh'],
            'how are you': ['I am fine, thank you for asking.'],
            'hello': ['Hello Sir, I am ready to assist you.'],
            'thank you jarvis': ['Welcome Sir!'],
            'introduce': ['I am a computer program chatbot AI that can understand and respond to human speech. I was created by Abhii Abhishek. I am named after the character Jarvis from the Iron Man movies.'],
            'who created you': ['I was created by Abhii Abhishek at NGF College, Palwal.'],
            'who was created you': ['I was created by Abhii Abhishek at NGF College, Palwal.'],
            'results': ['Anything else Sir?'],
            'default': ['I am not sure how to respond to that.']
        }

    def get_predefined_response(self, text):
        for key in self.responses:
            if key in text:
                return random.choice(self.responses[key])
        return None

    def process_input(self, user_input):
        text = user_input.lower().strip()
        
        if not text:
            return random.choice([
                "Yes Sir?",
                "I'm listening Sir.",
                "How may I assist you?",
                "Please tell me your command Sir."
            ])
        
        # Predefined responses check
        predefined = self.get_predefined_response(text)
        if predefined:
            return predefined

        # Web automation commands
        if "open youtube" in text:
            webbrowser.open("https://www.youtube.com")
            return "Opening YouTube Sir."
        if "open google" in text:
            webbrowser.open("https://www.google.com")
            return "Opening Google Sir."
        if any(phrase in text for phrase in ["play music", "play song", "favourite song"]):
            webbrowser.open("https://www.youtube.com/watch?v=r03GO2AlNUo&t=26s")
            return "Playing your favourite song Sir."
        if "open amazon" in text:
            webbrowser.open("https://www.amazon.com")
            return "Opening Amazon Sir."
        
        # Wikipedia lookup with exception handling
        if "wikipedia" in text:
            tts.speak("Searching Wikipedia...")
            query = user_input.replace("wikipedia", "").replace("Wikipedia", "").strip()
            try:
                result = wikipedia.summary(query, sentences=2)
                tts.speak("According to Wikipedia")
                return result
            except wikipedia.exceptions.DisambiguationError:
                return f"Multiple topics found for '{query}'. Please be more specific."
            except wikipedia.exceptions.PageError:
                return f"Sorry Sir, I couldn't find any Wikipedia page matching '{query}'."
            except Exception as e:
                return f"An error occurred while searching Wikipedia: {str(e)}"
        
        # Fallback to Gemini AI model
        if client:
            try:
                short_prompt = f"You are Chatbox who's named Jarvis & Answer in 1-2 short lines only, no extra details, no paragraphs. User asked: {user_input}"
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=short_prompt
                )
                return response.text.strip()
            except Exception as e:
                print(f"[Gemini API Exception] {e}")
                return "Sorry Sir, I am currently unable to connect to Gemini."
        else:
            return "Gemini API client is not initialized. Please provide a valid API key."

# ==========================================
# 4. CustomTkinter GUI Setup
# ==========================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

app = ctk.CTk()
app.title("Jarvis Assistant Chat")
app.geometry("460x640")

ai = JarvisBrain()

chat_frame = ctk.CTkScrollableFrame(app, width=430, height=520, fg_color="#111111")
chat_frame.pack(pady=10, padx=10)

def smooth_scroll():
    for i in range(5):
        app.after(i * 25, _scroll_to_bottom)

def _scroll_to_bottom():
    try:
        if hasattr(chat_frame, '_parent_canvas'):
            chat_frame._parent_canvas.yview_moveto(1.0)
    except Exception:
        pass

def add_bubble(message, sender="user"):
    if sender == "user":
        bubble_color = "#25D366"
        anchor_pos = "e"
        text_color = "black"
    else:
        bubble_color = "#2F2F2F"
        anchor_pos = "w"
        text_color = "white"

    bubble = ctk.CTkLabel(
        chat_frame, 
        text=message, 
        fg_color=bubble_color,
        corner_radius=18, 
        justify="left", 
        text_color=text_color,
        wraplength=260, 
        padx=12, 
        pady=8
    )
    bubble.pack(anchor=anchor_pos, pady=6, padx=6)
    smooth_scroll()

def bot_reply_thread(user_msg):
    reply = ai.process_input(user_msg)
    
    # Update GUI safely on the main thread
    app.after(0, lambda: add_bubble(reply, "bot"))
    
    # Speak reply via the queue-based TTS engine
    tts.speak(reply)

    # Persist log
    save_chat_history(user_msg, reply)

bottom_frame = ctk.CTkFrame(app, fg_color="#0D0D0D", corner_radius=0)
bottom_frame.pack(fill="x", padx=10, pady=5)

entry = ctk.CTkEntry(
    bottom_frame, 
    placeholder_text="Type your message...", 
    width=315,
    corner_radius=22, 
    fg_color="#222222", 
    text_color="white",
    border_width=2, 
    border_color="#25D366"
)
entry.pack(side="left", padx=5, pady=8)

def send_message(event=None):
    user_msg = entry.get().strip()
    if not user_msg:
        add_bubble("...", "user")
        entry.delete(0, ctk.END)
        threading.Thread(target=bot_reply_thread, args=(" ",), daemon=True).start()
        return

    add_bubble(user_msg, "user")
    entry.delete(0, ctk.END)

    if user_msg.lower() in ["exit", "quit", "bye", "close", "stop"]:
        add_bubble("Goodbye Sir, shutting down...", "bot")
        tts.speak("Goodbye Sir, shutting down")
        app.after(1000, app.destroy)
        return

    threading.Thread(target=bot_reply_thread, args=(user_msg,), daemon=True).start()

entry.bind("<Return>", send_message)

send_btn = ctk.CTkButton(
    bottom_frame, 
    text="Send", 
    width=80, 
    corner_radius=22,
    fg_color="#25D366", 
    text_color="black",
    command=send_message
)
send_btn.pack(side="right", padx=5)

if __name__ == "__main__":
    app.mainloop()
