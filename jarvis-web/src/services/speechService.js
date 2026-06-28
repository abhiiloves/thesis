// Browser Web Speech API Service

class SpeechService {
  constructor() {
    this.synth = typeof window !== 'undefined' && 'speechSynthesis' in window ? window.speechSynthesis : null;
    this.recognition = null;
    this.initRecognition();
  }

  initRecognition() {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = 'en-US';
      }
    }
  }

  speak(text, onEndCallback) {
    if (!this.synth || !text) return;

    // Cancel ongoing speech
    this.synth.cancel();

    // Remove code blocks or special markdown characters for natural speech
    const cleanText = text.replace(/```[\s\S]*?```/g, 'Code block output omitted.').replace(/[*_#`~]/g, '');

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    // Try selecting a natural English voice
    const voices = this.synth.getVoices();
    const preferredVoice = voices.find(v => (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('David')) && v.lang.startsWith('en'));
    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }

    if (onEndCallback) {
      utterance.onend = onEndCallback;
      utterance.onerror = onEndCallback;
    }

    this.synth.speak(utterance);
  }

  stopSpeech() {
    if (this.synth) {
      this.synth.cancel();
    }
  }

  startListening(onResultCallback, onErrorCallback) {
    if (!this.recognition) {
      if (onErrorCallback) onErrorCallback('Speech recognition is not supported in this browser.');
      return;
    }

    this.recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      if (onResultCallback) onResultCallback(transcript);
    };

    this.recognition.onerror = (event) => {
      if (onErrorCallback) onErrorCallback(event.error);
    };

    try {
      this.recognition.start();
    } catch (err) {
      console.warn('Recognition already started or error:', err);
    }
  }

  stopListening() {
    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (err) {
        console.warn(err);
      }
    }
  }
}

export const speechService = new SpeechService();
