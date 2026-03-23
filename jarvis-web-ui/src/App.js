import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  Send, Mic, MicOff, Volume2, Globe, Cloud, 
  Newspaper, Youtube, Sun, Moon, Languages 
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
  const [currentTime, setCurrentTime] = useState('');
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [activeTab, setActiveTab] = useState('chat');
  
  const messagesEndRef = useRef(null);
  const audioRef = useRef(null);

  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Update time every second
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
      }));
    };
    
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Fetch news on load
  useEffect(() => {
    fetchNews();
  }, []);

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = { role: 'user', content: inputMessage };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        message: inputMessage,
        language: language
      });

      const aiMessage = { 
        role: 'assistant', 
        content: response.data.response 
      };
      setMessages(prev => [...prev, aiMessage]);

      // Play TTS if available
      playTTS(response.data.response);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please try again.' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const playTTS = async (text) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/tts`, {
        message: text,
        language: language
      }, {
        responseType: 'blob'
      });

      const audioUrl = URL.createObjectURL(response.data);
      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        audioRef.current.play();
      }
    } catch (error) {
      console.error('TTS Error:', error);
    }
  };

  const fetchWeather = async (city) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/weather`, {
        city: city,
        language: language
      });
      setWeather(response.data);
    } catch (error) {
      console.error('Weather Error:', error);
    }
  };

  const fetchNews = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/news`);
      setNews(response.data.news.slice(0, 5));
    } catch (error) {
      console.error('News Error:', error);
    }
  };

  const searchYoutube = async (query) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/youtube/search`, {
        query: query
      });
      return response.data.videos;
    } catch (error) {
      console.error('YouTube Error:', error);
      return [];
    }
  };

  const toggleLanguage = async () => {
    const newLang = language === 'en' ? 'hi' : 'en';
    try {
      await axios.post(`${API_BASE_URL}/language`, {
        language: newLang
      });
      setLanguage(newLang);
    } catch (error) {
      console.error('Language Error:', error);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return language === 'hi' ? 'सुप्रभात' : 'Good Morning';
    if (hour < 17) return language === 'hi' ? 'नमस्कार' : 'Good Afternoon';
    if (hour < 20) return language === 'hi' ? 'शुभ संध्या' : 'Good Evening';
    return language === 'hi' ? 'शुभ रात्रि' : 'Good Night';
  };

  return (
    <div className={`app ${isDarkMode ? 'dark' : 'light'}`}>
      <audio ref={audioRef} style={{ display: 'none' }} />
      
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <div className="logo-container">
            <div className="logo-circle">J</div>
            <h1 className="app-title">Jarvis AI</h1>
          </div>
          <span className="status-indicator">●</span>
        </div>
        
        <div className="header-center">
          <span className="current-time">{currentTime}</span>
          <span className="greeting">{getGreeting()}</span>
        </div>
        
        <div className="header-right">
          <button 
            className="icon-button" 
            onClick={toggleLanguage}
            title={language === 'en' ? 'Switch to Hindi' : 'Switch to English'}
          >
            <Languages size={20} />
            <span className="lang-label">{language.toUpperCase()}</span>
          </button>
          <button 
            className="icon-button" 
            onClick={() => setIsDarkMode(!isDarkMode)}
          >
            {isDarkMode ? <Sun size={20} /> : <Moon size={20} />}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="main-content">
        {/* Sidebar */}
        <aside className="sidebar">
          <div className="sidebar-tabs">
            <button 
              className={`tab-button ${activeTab === 'chat' ? 'active' : ''}`}
              onClick={() => setActiveTab('chat')}
            >
              <Send size={18} />
              <span>Chat</span>
            </button>
            <button 
              className={`tab-button ${activeTab === 'weather' ? 'active' : ''}`}
              onClick={() => {
                setActiveTab('weather');
                if (!weather) fetchWeather('New Delhi');
              }}
            >
              <Cloud size={18} />
              <span>Weather</span>
            </button>
            <button 
              className={`tab-button ${activeTab === 'news' ? 'active' : ''}`}
              onClick={() => setActiveTab('news')}
            >
              <Newspaper size={18} />
              <span>News</span>
            </button>
            <button 
              className={`tab-button ${activeTab === 'youtube' ? 'active' : ''}`}
              onClick={() => setActiveTab('youtube')}
            >
              <Youtube size={18} />
              <span>YouTube</span>
            </button>
          </div>

          {/* Quick Weather Widget */}
          <div className="quick-widget">
            <h3>Quick Weather</h3>
            <input
              type="text"
              placeholder="Enter city..."
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  fetchWeather(e.target.value);
                }
              }}
              className="widget-input"
            />
            {weather && (
              <div className="weather-summary">
                <h4>{weather.city}</h4>
                <p className="temp">{weather.temperature}°C</p>
                <p className="condition">{weather.condition}</p>
              </div>
            )}
          </div>

          {/* Quick News */}
          <div className="quick-widget">
            <h3>Latest News</h3>
            <div className="news-list-compact">
              {news.slice(0, 3).map((item, index) => (
                <a 
                  key={index} 
                  href={item.link} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="news-item-compact"
                >
                  {item.title}
                </a>
              ))}
            </div>
          </div>
        </aside>

        {/* Main Chat Area */}
        <main className="chat-container">
          {activeTab === 'chat' && (
            <>
              <div className="messages-container">
                {messages.length === 0 && (
                  <div className="welcome-message">
                    <div className="welcome-icon">👋</div>
                    <h2>Welcome to Jarvis AI</h2>
                    <p>Your personal AI assistant is ready to help!</p>
                    <div className="suggestion-chips">
                      <button onClick={() => setInputMessage("What can you do?")}>
                        What can you do?
                      </button>
                      <button onClick={() => setInputMessage("Tell me a joke")}>
                        Tell me a joke
                      </button>
                      <button onClick={() => setInputMessage("What's the weather?")}>
                        What's the weather?
                      </button>
                    </div>
                  </div>
                )}

                {messages.map((msg, index) => (
                  <div 
                    key={index} 
                    className={`message ${msg.role}`}
                  >
                    <div className="message-avatar">
                      {msg.role === 'user' ? '👤' : '🤖'}
                    </div>
                    <div className="message-content">
                      <p>{msg.content}</p>
                    </div>
                  </div>
                ))}

                {isLoading && (
                  <div className="message assistant">
                    <div className="message-avatar">🤖</div>
                    <div className="message-content">
                      <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              <div className="input-container">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={language === 'hi' ? 'अपना संदेश टाइप करें...' : 'Type your message...'}
                  className="message-input"
                  rows="1"
                />
                <button 
                  onClick={sendMessage} 
                  disabled={isLoading || !inputMessage.trim()}
                  className="send-button"
                >
                  <Send size={20} />
                </button>
              </div>
            </>
          )}

          {activeTab === 'weather' && (
            <div className="tab-content">
              <h2>Weather Information</h2>
              <input
                type="text"
                placeholder="Enter city name..."
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    fetchWeather(e.target.value);
                  }
                }}
                className="search-input"
              />
              {weather && (
                <div className="weather-details">
                  <h3>{weather.city}</h3>
                  <div className="weather-main">
                    <p className="temperature">{weather.temperature}°C</p>
                    <p className="condition">{weather.condition}</p>
                  </div>
                  <div className="weather-info">
                    <p>Humidity: {weather.humidity}%</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'news' && (
            <div className="tab-content">
              <h2>Latest News</h2>
              <div className="news-grid">
                {news.map((item, index) => (
                  <a 
                    key={index}
                    href={item.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="news-card"
                  >
                    <h3>{item.title}</h3>
                    {item.description && <p>{item.description}</p>}
                    <span className="news-date">{new Date(item.pubDate).toLocaleDateString()}</span>
                  </a>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'youtube' && (
            <div className="tab-content">
              <h2>YouTube Search</h2>
              <input
                type="text"
                placeholder="Search for videos..."
                onKeyPress={async (e) => {
                  if (e.key === 'Enter') {
                    const videos = await searchYoutube(e.target.value);
                    // Display videos (you can add state to show results)
                    console.log(videos);
                  }
                }}
                className="search-input"
              />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
