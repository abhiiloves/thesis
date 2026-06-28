import { GoogleGenAI } from '@google/genai';

class JarvisBrain {
  constructor() {
    this.responses = {
      'hi': ['Hello! Sir, I am ready to assist you.', 'Hi sir, I am ready to assist you.'],
      'greetings': ['Hello! Sir, I am ready to assist you.'],
      'your owner': ['Abhii Abhishek and Bhanu Pratap Singh.'],
      'how are you': ['I am operating at peak efficiency, thank you for asking Sir.'],
      'hello': ['Hello Sir, I am ready to assist you.'],
      'thank you jarvis': ['Always a pleasure to assist you, Sir!'],
      'introduce': ['I am Jarvis, an advanced AI chatbot assistant designed by Abhii Abhishek. I process queries, run automated tasks, and converse naturally.'],
      'who created you': ['I was created by Abhii Abhishek at NGF College, Palwal.'],
    };
  }

  // Get stored long-term memories across all chats
  getMemories() {
    try {
      const saved = localStorage.getItem('JARVIS_LONG_TERM_MEMORY');
      return saved ? JSON.parse(saved) : [];
    } catch (e) {
      return [];
    }
  }

  // Save a new fact/memory into global persistent storage
  saveMemory(fact) {
    const memories = this.getMemories();
    if (!memories.includes(fact)) {
      memories.push(fact);
      localStorage.setItem('JARVIS_LONG_TERM_MEMORY', JSON.stringify(memories));
    }
  }

  // Automatically check if user input is asking to remember something
  detectAndStoreMemory(text) {
    const lower = text.toLowerCase();
    
    if (lower.includes("remember that") || lower.includes("remember this") || lower.includes("remember ")) {
      const cleanFact = text.replace(/remember that|remember this|remember/gi, "").trim();
      if (cleanFact) {
        this.saveMemory(cleanFact);
        return `Got it, Sir! I have saved to my long-term memory: "${cleanFact}". I will remember this across all our chats.`;
      }
    }

    if (lower.includes("my friend") || lower.includes("my name is") || lower.includes("i live in")) {
      this.saveMemory(text);
    }

    return null;
  }

  getPredefinedResponse(input) {
    const lower = input.toLowerCase();
    for (let key in this.responses) {
      if (lower.includes(key)) {
        const list = this.responses[key];
        return list[Math.floor(Math.random() * list.length)];
      }
    }
    return null;
  }

  async processInput(userInput, customApiKey = '') {
    const text = userInput.trim();
    const lower = text.toLowerCase();

    if (!text) {
      const prompts = ["Yes Sir?", "I'm listening Sir.", "How may I assist you?"];
      return prompts[Math.floor(Math.random() * prompts.length)];
    }

    // 1. Check if user explicitly asked to remember something
    const memoryConfirmation = this.detectAndStoreMemory(text);
    if (memoryConfirmation) {
      return memoryConfirmation;
    }

    // 2. Web Automation Commands
    if (lower.includes("open youtube")) {
      window.open("https://www.youtube.com", "_blank");
      return "Opening YouTube Sir.";
    }
    if (lower.includes("open google")) {
      window.open("https://www.google.com", "_blank");
      return "Opening Google Sir.";
    }
    if (lower.includes("play music") || lower.includes("play song")) {
      window.open("https://www.youtube.com/watch?v=r03GO2AlNUo&t=26s", "_blank");
      return "Playing your favourite song Sir.";
    }

    // 3. Predefined quick responses
    const predefined = this.getPredefinedResponse(lower);
    if (predefined) {
      return predefined;
    }

    // 4. Gemini AI with Cross-Session Long-Term Memory Injection
    const apiKey = customApiKey || localStorage.getItem('GEMINI_API_KEY') || import.meta.env.VITE_GEMINI_API_KEY || '';

    if (!apiKey) {
      return "Sir, please configure your Gemini API Key in Settings to enable AI responses and memory retrieval.";
    }

    try {
      const ai = new GoogleGenAI({ apiKey });
      const memories = this.getMemories();

      let memoryContext = "";
      if (memories.length > 0) {
        memoryContext = `\n[GLOBAL LONG-TERM MEMORY STORED ABOUT USER ACROSS ALL CHATS]:\n- ${memories.join('\n- ')}\nUse this information to answer user questions about facts, names, or details they previously told you to remember.`;
      }

      const prompt = `You are Jarvis, an advanced highly intelligent AI assistant. Keep answers concise, clear, and direct.${memoryContext}\n\nUser asked: ${userInput}`;

      const response = await ai.models.generateContent({
        model: 'gemini-2.5-flash',
        contents: prompt,
      });

      return response.text ? response.text.strip ? response.text.strip() : response.text : "I processed your request, Sir.";
    } catch (error) {
      console.error("Gemini AI API Error:", error);
      return `Sorry Sir, I encountered an issue: ${error.message || 'Check connection.'}`;
    }
  }
}

export const jarvisBrain = new JarvisBrain();
