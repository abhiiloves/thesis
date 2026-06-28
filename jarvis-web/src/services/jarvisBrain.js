import { GoogleGenAI } from '@google/genai';

class JarvisBrain {
  constructor() {
    this.responses = {
      'hi': ['Hello! Sir, I am ready to assist you.', 'Hi sir, I am ready to assist you.', 'Hello Sir, I am ready to assist you.'],
      'greetings': ['Hello! Sir, I am ready to assist you.', 'Hi sir, I am ready to assist you.'],
      'my friends name': ['Vikas Kumar, Kushagra, and Pradeep.'],
      'your owner': ['Abhii Abhishek and Bhanu Pratap Singh.'],
      'how are you': ['I am operating at peak efficiency, thank you for asking Sir.'],
      'hello': ['Hello Sir, I am ready to assist you.'],
      'thank you jarvis': ['Always a pleasure to assist you, Sir!'],
      'introduce': ['I am Jarvis, an advanced AI chatbot assistant designed by Abhii Abhishek. I process queries, run automated tasks, and converse naturally.'],
      'who created you': ['I was created by Abhii Abhishek at NGF College, Palwal.'],
      'results': ['Anything else Sir?'],
      'default': ['I am not sure how to respond to that Sir.']
    };
  }

  getPredefinedResponse(input) {
    const lower = input.toLowerCase().strip ? input.toLowerCase().strip() : input.toLowerCase();
    for (let key in this.responses) {
      if (lower.includes(key)) {
        const list = this.responses[key];
        return list[Math.floor(Math.random() * list.length)];
      }
    }
    return null;
  }

  async processInput(userInput, customApiKey = '') {
    const text = userInput.trim().toLowerCase();

    if (!text) {
      const prompts = [
        "Yes Sir?",
        "I'm listening Sir.",
        "How may I assist you?",
        "Please tell me your command Sir."
      ];
      return prompts[Math.floor(Math.random() * prompts.length)];
    }

    // 1. Check Predefined responses
    const predefined = this.getPredefinedResponse(text);
    if (predefined) {
      return predefined;
    }

    // 2. Web Automation Commands
    if (text.includes("open youtube")) {
      window.open("https://www.youtube.com", "_blank");
      return "Opening YouTube Sir.";
    }
    if (text.includes("open google")) {
      window.open("https://www.google.com", "_blank");
      return "Opening Google Sir.";
    }
    if (text.includes("play music") || text.includes("play song") || text.includes("favourite song")) {
      window.open("https://www.youtube.com/watch?v=r03GO2AlNUo&t=26s", "_blank");
      return "Playing your favourite song Sir.";
    }
    if (text.includes("open amazon")) {
      window.open("https://www.amazon.com", "_blank");
      return "Opening Amazon Sir.";
    }

    // 3. Fallback to Gemini AI (Direct API call using Google GenAI SDK)
    const apiKey = customApiKey || localStorage.getItem('GEMINI_API_KEY') || import.meta.env.VITE_GEMINI_API_KEY || '';

    if (!apiKey) {
      return "Sir, please configure your Gemini API Key in the Settings panel or set the environment variable to enable full AI capabilities.";
    }

    try {
      const ai = new GoogleGenAI({ apiKey });
      const prompt = `You are Jarvis, an advanced highly intelligent AI assistant inspired by Iron Man. Keep answers concise, clear, and elegant. User asked: ${userInput}`;
      
      const response = await ai.models.generateContent({
        model: 'gemini-2.5-flash',
        contents: prompt,
      });

      return response.text ? response.text.trim() : "I processed your request, Sir.";
    } catch (error) {
      console.error("Gemini AI API Error:", error);
      return `Sorry Sir, I encountered an issue connecting to Gemini AI: ${error.message || 'Check your API Key or Network Connection.'}`;
    }
  }
}

export const jarvisBrain = new JarvisBrain();
