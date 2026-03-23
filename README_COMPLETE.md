# Jarvis A.I - Complete Setup Guide

## ✅ Azure OpenAI Integration Complete!

Your Jarvis AI assistant is now fully configured and working!

### 🔧 Current Configuration

- **Azure Endpoint**: https://bhanu-mmjcqyw0-eastus2.openai.azure.com/
- **Model**: gpt-5.2-bhanu-model (GPT-5.2 Chat Latest)
- **API Version**: 2024-02-15-preview
- **Status**: ✅ Connected and working

### 🚀 How to Run Jarvis

Simply run:
```powershell
python Jarvis.py
```

Jarvis will automatically detect if voice input is available:
- **If PyAudio is installed**: Voice input mode (speak commands)
- **If PyAudio is missing**: Text input mode (type commands)

### 💬 Available Commands

#### Website Commands
- "open youtube" - Opens YouTube
- "open google" - Opens Google
- "open wikipedia" - Opens Wikipedia
- "open amazon" - Opens Amazon
- "open netflix" - Opens Netflix
- "open linkedin" - Opens LinkedIn
- "open jiocinema" - Opens JioCinema
- "open sonyliv" - Opens SonyLiv
- "open chat gpt" - Opens ChatGPT

#### Information Commands
- "the time" - Get current time with greeting
- "current date" - Get today's date
- Ask any question - Chat with Jarvis using Azure OpenAI

#### Special Commands
- "Using AI [your question]" - Save AI response to a file
- "reset chat" - Clear conversation history
- "jarvis stop" - Exit the program

#### Additional Features (requires API keys)
- "songs/movies/videos" - Search YouTube (needs YouTube API key)
- "news" - Get latest news (needs News API key)
- "what is the weather" - Get weather info (needs Weather API key)

### 🎤 Voice Input Setup (Optional)

If you want to use voice commands, you need to install PyAudio. However, this is optional - Jarvis works perfectly with text input!

#### For Voice Features:
PyAudio installation on Windows requires special steps. Try one of these methods:

**Method 1: Download pre-compiled wheel**
1. Go to: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
2. Download the wheel file matching your Python version and system (e.g., `PyAudio‑0.2.11‑cp314‑cp314‑win_amd64.whl` for Python 3.14 64-bit)
3. Install it:
   ```powershell
   pip install path\to\downloaded\PyAudio‑0.2.11‑cp314‑cp314‑win_amd64.whl
   ```

**Method 2: Use conda (if you have Anaconda/Miniconda)**
```powershell
conda install pyaudio
```

### 📁 Project Files

- **Jarvis.py** - Main program (auto-detects voice/text mode)
- **Jarvis_text.py** - Text-only version (guaranteed to work)
- **config.py** - Azure OpenAI configuration
- **project.py** - Email generation example
- **test_azure_openai.py** - Quick connection test
- **test_jarvis_features.py** - Comprehensive feature test
- **test_microphone.py** - Test microphone availability

### 🧪 Testing

#### Test Azure OpenAI connection:
```powershell
python test_azure_openai.py
```

#### Test all Jarvis features:
```powershell
python test_jarvis_features.py
```

#### Test microphone setup:
```powershell
python test_microphone.py
```

### ✨ What's Working Now

✅ Azure OpenAI integration with GPT-5.2  
✅ Text-to-speech responses  
✅ Website opening commands  
✅ Time and date queries  
✅ AI conversation with context memory  
✅ AI response file saving  
✅ Automatic fallback to text input if voice unavailable  

### 📝 Example Usage

```
Welcome to Jarvis A.I (Text Mode)
You: hello
Jarvis: Hello! I'm Jarvis, your AI assistant. How can I help you today?

You: the time
Sir, the time is 13:45
Good Afternoon Sir!

You: open youtube
Opening youtube sir...
[YouTube opens in browser]

You: what is python
Jarvis: Python is a high-level, interpreted programming language...

You: jarvis stop
Goodbye!
```

### 🔑 Optional API Keys

To enable additional features, add these API keys to Jarvis.py:

1. **YouTube API** (line ~27): For video search
   - Get it from: https://console.cloud.google.com/apis/credentials

2. **News API** (line ~70): For news headlines
   - Get it from: https://newsapi.org/

3. **Weather API** (line ~96): For weather info
   - Get it from: https://www.weatherapi.com/

### 🛠️ Troubleshooting

**"Could not find PyAudio"**
- This is  normal! Jarvis will use text input instead.
- Voice input is optional - text mode works perfectly.

**"Connection error" or "API error"**
- Check your internet connection
- Verify Azure OpenAI credentials in config.py
- Run `python test_azure_openai.py` to diagnose

**Text-to-speech not working**
- Check if pyttsx3 is installed: `pip install pyttsx3`
- On some systems, you may need to install espeak

### 📦 Dependencies

```
openai>=1.10.0          ✅ Installed
SpeechRecognition>=3.10.0  ✅ Installed
pyttsx3>=2.90           ✅ Installed
requests>=2.31.0        ✅ Installed
pyaudio>=0.2.13         ⚠ Optional (for voice input)
```

---

**Enjoy your AI assistant! 🎉**

For questions or issues, check the test files or run diagnostics.
