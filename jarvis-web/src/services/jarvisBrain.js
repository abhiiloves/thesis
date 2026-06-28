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
      'introduce': ['I am Jarvis, an advanced AI chatbot assistant designed by Abhii Abhishek. I process queries, run automated tasks, analyze images, generate art, and set alarms.'],
      'who created you': ['I was created by Abhii Abhishek at NGF College, Palwal.'],
    };
  }

  getMemories() {
    try {
      const saved = localStorage.getItem('JARVIS_LONG_TERM_MEMORY');
      return saved ? JSON.parse(saved) : [];
    } catch (e) {
      return [];
    }
  }

  saveMemory(fact) {
    const memories = this.getMemories();
    if (!memories.includes(fact)) {
      memories.push(fact);
      localStorage.setItem('JARVIS_LONG_TERM_MEMORY', JSON.stringify(memories));
    }
  }

  detectAndStoreMemory(text) {
    const lower = text.toLowerCase();
    if (lower.includes("remember that") || lower.includes("remember this") || lower.includes("remember ")) {
      const cleanFact = text.replace(/remember that|remember this|remember/gi, "").trim();
      if (cleanFact) {
        this.saveMemory(cleanFact);
        return `Got it, Sir! I have saved to my long-term memory: "${cleanFact}".`;
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

  // Play alarm audio chime
  playAlarmChime() {
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
      osc.frequency.setValueAtTime(880, audioCtx.currentTime + 0.2); // A5
      gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 1.5);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 1.5);
    } catch (e) {
      console.warn("Audio Context error:", e);
    }
  }

  // Handle live weather fetching
  async fetchLiveWeather(city) {
    try {
      const res = await fetch(`https://wttr.in/${encodeURIComponent(city)}?format=j1`);
      if (!res.ok) throw new Error("Weather service unreachable");
      const data = await res.json();
      const current = data.current_condition[0];
      const tempC = current.temp_C;
      const desc = current.weatherDesc[0].value;
      const humidity = current.humidity;
      const windSpeed = current.windspeedKmph;

      return `Current Weather in ${city.toUpperCase()}: ${tempC}°C, ${desc}. Humidity: ${humidity}%, Wind: ${windSpeed} km/h.`;
    } catch (e) {
      return `Sorry Sir, I could not fetch live weather data for ${city} right now.`;
    }
  }

  async processInput(userInput, attachments = [], customApiKey = '') {
    const text = userInput.trim();
    const lower = text.toLowerCase();

    // 1. Check AI Image Generation commands
    if (lower.startsWith("generate image") || lower.startsWith("draw") || lower.startsWith("create image") || lower.startsWith("make an image")) {
      const imagePrompt = text.replace(/generate image of|generate image|draw|create image of|create image|make an image of|make an image/gi, "").trim();
      if (imagePrompt) {
        const imageUrl = `https://pollinations.ai/p/${encodeURIComponent(imagePrompt)}?width=1024&height=1024&seed=${Math.floor(Math.random() * 100000)}&nologo=true`;
        return `Here is your generated image for **"${imagePrompt}"**, Sir:\n\n![${imagePrompt}](${imageUrl})`;
      }
    }

    // 2. Check Reminder / Alarm commands
    const reminderMatch = lower.match(/(?:remind me in|timer|alarm for)\s+(\d+)\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?)\s*(?:to|for)?\s*(.*)/i);
    if (reminderMatch) {
      const num = parseInt(reminderMatch[1]);
      const unit = reminderMatch[2].toLowerCase();
      const task = reminderMatch[3] || "your reminder";

      let multiplier = 1000;
      if (unit.startsWith("min")) multiplier = 60 * 1000;
      if (unit.startsWith("hour") || unit.startsWith("hr")) multiplier = 3600 * 1000;

      const durationMs = num * multiplier;

      setTimeout(() => {
        this.playAlarmChime();
        if ("Notification" in window && Notification.permission === "granted") {
          new Notification("JARVIS Reminder", { body: `Sir, time to: ${task}`, icon: "/favicon.ico" });
        } else {
          alert(`⏰ JARVIS REMINDER: Sir, time to ${task}!`);
        }
      }, durationMs);

      if ("Notification" in window && Notification.permission !== "granted") {
        Notification.requestPermission();
      }

      return `Alarm set Sir! I will remind you to "${task}" in ${num} ${unit}.`;
    }

    // 3. Check Live Weather queries
    if (lower.includes("weather in") || lower.includes("weather of")) {
      const cityMatch = text.match(/weather (?:in|of)\s+([a-zA-Z\s]+)/i);
      if (cityMatch && cityMatch[1]) {
        return await this.fetchLiveWeather(cityMatch[1].trim());
      }
    }

    // 4. Check memory detection
    const memoryConfirmation = this.detectAndStoreMemory(text);
    if (memoryConfirmation && attachments.length === 0) {
      return memoryConfirmation;
    }

    // 5. Web Automation commands
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

    // 6. Predefined responses (only if no attachments)
    if (attachments.length === 0) {
      const predefined = this.getPredefinedResponse(lower);
      if (predefined) return predefined;
    }

    // 7. Gemini AI with Vision & Document Multimodal context
    const apiKey = customApiKey || localStorage.getItem('GEMINI_API_KEY') || import.meta.env.VITE_GEMINI_API_KEY || '';
    if (!apiKey) {
      return "Sir, please configure your Gemini API Key in Settings to analyze files, images, or answer AI queries.";
    }

    try {
      const ai = new GoogleGenAI({ apiKey });
      const memories = this.getMemories();

      let memoryContext = "";
      if (memories.length > 0) {
        memoryContext = `\n[LONG-TERM MEMORY ABOUT USER]:\n- ${memories.join('\n- ')}\n`;
      }

      const contentsPayload = [];
      let promptText = `You are Jarvis, an advanced AI assistant inspired by Iron Man.${memoryContext}\nUser prompt: ${text || "Please analyze the attached files/images."}`;

      // Process attachments (Images / Documents)
      if (attachments.length > 0) {
        attachments.forEach(att => {
          if (att.type === 'image') {
            const base64Data = att.data.split(',')[1];
            contentsPayload.push({
              inlineData: {
                mimeType: att.mimeType,
                data: base64Data
              }
            });
          } else if (att.type === 'document') {
            promptText += `\n\n[ATTACHED FILE CONTEXT - ${att.name}]:\n${att.data.substring(0, 10000)}`;
          }
        });
      }

      contentsPayload.unshift(promptText);

      const response = await ai.models.generateContent({
        model: 'gemini-2.5-flash',
        contents: contentsPayload,
      });

      return response.text ? response.text.trim() : "I have processed your request, Sir.";
    } catch (error) {
      console.error("Gemini API Error:", error);
      return `Sorry Sir, error processing request: ${error.message || 'Check connection.'}`;
    }
  }
}

export const jarvisBrain = new JarvisBrain();
