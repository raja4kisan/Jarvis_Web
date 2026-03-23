import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  Send, Mic, MicOff, Volume2, Globe, Cloud, 
  Newspaper, Youtube, Sun, Moon, Languages,
  LogIn, Trophy, MessageSquare, Play, Square
} from 'lucide-react';
import './App.css';

const API_BASE_URL = process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [language, setLanguage] = useState('en');
  const [weather, setWeather] = useState(null);
  const [news, setNews] = useState([]);
  const [cricket, setCricket] = useState([]);
  const [currentTime, setCurrentTime] = useState('');
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [activeTab, setActiveTab] = useState('chat');
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceMode, setVoiceMode] = useState(false);
  
  const messagesEndRef = useRef(null);
  const audioRef = useRef(null);
  const recognitionRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Clock
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Initialize Speech Recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;

      recognitionRef.current.onstart = () => setIsListening(true);
      recognitionRef.current.onend = () => {
        setIsListening(false);
        // Restart if voice mode is on and we aren't speaking
        if (voiceMode && !isSpeaking) {
          setTimeout(() => {
            if (voiceMode && !isSpeaking) startListening();
          }, 500);
        }
      };

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInputMessage(transcript);
        handleSendMessage(transcript);
      };

      recognitionRef.current.onerror = (err) => {
        console.error('Speech error:', err);
        setIsListening(false);
      };
    }
  }, [voiceMode, isSpeaking]);

  // Auto-Start Experience
  useEffect(() => {
    const initJarvis = async () => {
      await fetchNews();
      await fetchCricket();
      
      // Auto-greeting
      const greeting = getGreeting();
      const initialMsg = { role: 'assistant', content: `Jarvis online. ${greeting} Sir. How can I help you?` };
      setMessages([initialMsg]);
      
      // Auto-speak greeting and enable voice mode
      setTimeout(() => {
        playTTS(initialMsg.content);
        setVoiceMode(true);
      }, 1000);
    };
    initJarvis();
  }, []);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 17) return 'Good Afternoon';
    return 'Good Evening';
  };

  const startListening = () => {
    if (recognitionRef.current && !isListening && !isSpeaking) {
      try {
        recognitionRef.current.lang = language === 'hi' ? 'hi-IN' : 'en-US';
        recognitionRef.current.start();
      } catch (e) {
        console.error('Start error:', e);
      }
    }
  };

  const handleSendMessage = async (msgOverride) => {
    const msg = msgOverride || inputMessage;
    if (!msg.trim()) return;

    setMessages(prev => [...prev, { role: 'user', content: msg }]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/chat`, { message: msg, language });
      const aiResponse = response.data.response;
      
      // Check if it's an error response
      if (response.data.error) {
        setMessages(prev => [...prev, { role: 'assistant', content: `⚠️ ${aiResponse}` }]);
        return;
      }

      setMessages(prev => [...prev, { role: 'assistant', content: aiResponse }]);
      
      if (voiceMode) {
        playTTS(aiResponse);
      }
    } catch (err) {
      console.error('Chat error:', err);
      setMessages(prev => [...prev, { role: 'assistant', content: "❌ Connection Error: Could not reach the server." }]);
    } finally {
      setIsLoading(false);
    }
  };

  const playTTS = async (text) => {
    if (isSpeaking) return;
    setIsSpeaking(true);
    
    try {
      const response = await axios.post(`${API_BASE_URL}/tts`, { message: text, language }, { responseType: 'blob' });
      const url = URL.createObjectURL(response.data);
      if (audioRef.current) {
        audioRef.current.src = url;
        audioRef.current.onended = () => {
          setIsSpeaking(false);
          if (voiceMode) startListening();
        };
        audioRef.current.play();
      }
    } catch (err) {
      console.error('TTS error:', err);
      setIsSpeaking(false);
    }
  };

  const fetchNews = async () => {
    try {
      const resp = await axios.get(`${API_BASE_URL}/news`);
      setNews(resp.data.news);
    } catch (e) { console.error(e); }
  };

  const fetchCricket = async () => {
    try {
      const resp = await axios.get(`${API_BASE_URL}/cricket/matches`);
      setCricket(resp.data.matches);
    } catch (e) { console.error(e); }
  };

  return (
    <div className="app">
      <audio ref={audioRef} style={{ display: 'none' }} />
      
      <header className="header">
        <div className="logo-container">
          <div className="logo-circle">J</div>
          <h1 className="app-title">Jarvis AI</h1>
        </div>
        
        <div className="header-center">
          <span className="current-time">{currentTime}</span>
          <span className="greeting">{getGreeting()}</span>
        </div>
        
        <div className="header-right">
          <button className="tab-button" onClick={() => setVoiceMode(!voiceMode)}>
            {voiceMode ? <Mic size={20} color="#10b981" /> : <MicOff size={20} />}
          </button>
        </div>
      </header>

      <div className="main-content">
        <aside className="sidebar">
          <div className="sidebar-tabs">
            <button className={`tab-button ${activeTab === 'chat' ? 'active' : ''}`} onClick={() => setActiveTab('chat')}>
              <MessageSquare size={18} /> <span>Chat</span>
            </button>
            <button className={`tab-button ${activeTab === 'cricket' ? 'active' : ''}`} onClick={() => { setActiveTab('cricket'); fetchCricket(); }}>
              <Trophy size={18} /> <span>Cricket</span>
            </button>
            <button className={`tab-button ${activeTab === 'news' ? 'active' : ''}`} onClick={() => setActiveTab('news')}>
              <Newspaper size={18} /> <span>News</span>
            </button>
          </div>

          <button className="google-auth-btn">
            <LogIn size={18} /> Sign in with Google
          </button>
        </aside>

        <main className="chat-container">
          {activeTab === 'chat' && (
            <>
              <div className="messages-container">
                {messages.map((m, i) => (
                  <div key={i} className={`message ${m.role}`}>
                    <div className="message-avatar">{m.role === 'user' ? '👤' : '🤖'}</div>
                    <div className="message-content">{m.content}</div>
                  </div>
                ))}
                {isLoading && <div className="message assistant"><div className="message-content">...</div></div>}
                <div ref={messagesEndRef} />
              </div>

              <div className="input-area-wrapper">
                <div 
                  className={`gemini-mic-container ${isListening ? 'listening' : ''}`}
                  onClick={() => { setVoiceMode(true); startListening(); }}
                >
                  <div className="mic-ring"></div>
                  <div className="mic-circle">
                    {isSpeaking ? <Volume2 size={24} /> : (isListening ? <Mic size={24} /> : <MicOff size={24} />)}
                  </div>
                </div>

                <div className="input-container">
                  <input 
                    className="message-input"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Ask Jarvis anything..."
                  />
                  <button className="send-button" onClick={() => handleSendMessage()}>
                    <Send size={20} />
                  </button>
                </div>
              </div>
            </>
          )}

          {activeTab === 'cricket' && (
            <div className="tab-content">
              <h2 style={{marginBottom:'20px'}}>Live Cricket Scores</h2>
              <div className="cricket-grid">
                {cricket.map(m => (
                  <div key={m.id} className="cricket-card">
                    <div className="status">{m.status}</div>
                    <h4>{m.name}</h4>
                    <p style={{marginTop:'10px', fontWeight:'700'}}>{m.teams[0]} vs {m.teams[1]}</p>
                    <p style={{fontSize:'0.9rem', color:'var(--text-muted)'}}>{m.venue}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'news' && (
            <div className="tab-content">
              <h2 style={{marginBottom:'20px'}}>Top Headlines</h2>
              <div className="news-grid">
                {news.map((n, i) => (
                  <a key={i} href={n.link} target="_blank" rel="noreferrer" className="news-card">
                    <h4>{n.title}</h4>
                    <p>{n.description}</p>
                  </a>
                ))}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
