# Jarvis AI - FastAPI Backend for Cloud Deployment
import os
import datetime
import requests
from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import edge_tts
import tempfile
import asyncio
from openai import OpenAI
import logging
from config import apikey, api_base, api_version, deployment_name, youtube_api_key, weather_api_key, news_api_key, cricket_api_key, openrouter_api_key, supabase_url, supabase_key, supabase_service_key

# Gmail API imports
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
import base64
import pickle

# Supabase imports
from supabase import create_client, Client
from jose import jwt, JWTError
import json

# Configure logging to show in Railway logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Jarvis AI API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenRouter client (OpenAI-compatible API)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=openrouter_api_key
)

# Initialize Supabase client
supabase: Client = None
if supabase_url and supabase_key:
    try:
        supabase = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase: {e}")
else:
    logger.warning("Supabase credentials not configured")

# Models
class ChatRequest(BaseModel):
    message: str
    language: Optional[str] = "en"

class WeatherRequest(BaseModel):
    city: str
    language: Optional[str] = "en"

class YoutubeRequest(BaseModel):
    query: str

class TTSRequest(BaseModel):
    message: str
    language: Optional[str] = "en"

class AuthRequest(BaseModel):
    access_token: str

class ChatRequestAuth(BaseModel):
    message: str
    access_token: str
    session_id: Optional[str] = None
    language: Optional[str] = "en"

class NewSessionRequest(BaseModel):
    title: Optional[str] = "New Chat"

# Global context memory (Simulated for single user, recommend Redis for multi-user)
chat_history = []

# Helper function to verify Supabase JWT token
def verify_token(token: str):
    """Verify Supabase JWT token and return user data"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        # Verify token with Supabase
        user_response = supabase.auth.get_user(token)
        if user_response and user_response.user:
            return user_response.user
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

# Gmail API Configuration
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    """Authenticate with Gmail API using OAuth2"""
    creds = None
    token_path = 'token.json'
    credentials_path = 'credentials.json'
    
    # Check if token.json exists
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, GMAIL_SCOPES)
        except Exception as e:
            logger.error(f"Error loading token.json: {e}")
            creds = None
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(GoogleRequest())
                logger.info("Gmail token refreshed successfully")
            except Exception as e:
                logger.error(f"Error refreshing token: {e}")
                creds = None
        
        if not creds:
            if not os.path.exists(credentials_path):
                logger.error("credentials.json not found. Please follow GMAIL_SETUP_GUIDE.md")
                return None
            try:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, GMAIL_SCOPES)
                creds = flow.run_local_server(port=0)
                logger.info("Gmail OAuth flow completed successfully")
            except Exception as e:
                logger.error(f"OAuth flow error: {e}")
                return None
        
        # Save credentials for next run
        try:
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
            logger.info("Gmail credentials saved to token.json")
        except Exception as e:
            logger.error(f"Error saving token: {e}")
    
    return creds

def read_gmail_emails(max_results=10, query=""):
    """Read emails from Gmail inbox"""
    try:
        creds = authenticate_gmail()
        if not creds:
            return {"emails": [], "error": "Gmail authentication failed. Please follow GMAIL_SETUP_GUIDE.md"}
        
        service = build('gmail', 'v1', credentials=creds)
        
        # Get messages
        results = service.users().messages().list(
            userId='me', 
            maxResults=max_results,
            q=query
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return {"emails": [], "count": 0, "message": "No emails found"}
        
        emails = []
        for msg in messages:
            try:
                message = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
                
                # Extract headers
                headers = message['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
                date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
                
                # Check if unread
                labels = message.get('labelIds', [])
                is_unread = 'UNREAD' in labels
                
                # Get snippet (preview)
                snippet = message.get('snippet', '')
                
                emails.append({
                    "id": msg['id'],
                    "subject": subject,
                    "from": sender,
                    "date": date,
                    "snippet": snippet,
                    "unread": is_unread
                })
            except Exception as e:
                logger.error(f"Error processing email {msg['id']}: {e}")
                continue
        
        return {"emails": emails, "count": len(emails)}
    
    except Exception as e:
        logger.error(f"Gmail API error: {e}")
        return {"emails": [], "error": str(e)}

@app.get("/")
async def root():
    """Serve landing page with Google Sign-In"""
    index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "message": "Jarvis AI Landing Page",
        "status": "online",
        "error": "Landing page not found"
    }

@app.get("/chat")
async def chat_interface():
    """Serve main Jarvis chat interface (requires authentication)"""
    web_ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web-ui.html")
    if os.path.exists(web_ui_path):
        return FileResponse(web_ui_path)
    raise HTTPException(status_code=404, detail="Chat interface not found")

@app.get("/health")
async def health():
    return {"status": "healthy"}

# ============ AUTHENTICATION ENDPOINTS ============

@app.post("/auth/verify")
async def verify_auth(auth_request: AuthRequest):
    """Verify user authentication token"""
    try:
        user = verify_token(auth_request.access_token)
        return {
            "authenticated": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "user_metadata": user.user_metadata
            }
        }
    except HTTPException as e:
        return {"authenticated": False, "error": str(e.detail)}

@app.post("/auth/google")
async def google_auth():
    """Initiate Google OAuth flow - returns Supabase auth URL"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        # Return auth config for frontend to handle
        return {
            "provider": "google",
            "supabase_url": supabase_url,
            "message": "Use Supabase client on frontend to sign in with Google"
        }
    except Exception as e:
        logger.error(f"Google auth error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ CHAT SESSION ENDPOINTS ============

@app.post("/sessions/new")
async def create_session(auth_request: AuthRequest, session_data: NewSessionRequest):
    """Create a new chat session"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        user = verify_token(auth_request.access_token)
        
        # Create new chat session
        response = supabase.table("chat_sessions").insert({
            "user_id": user.id,
            "title": session_data.title
        }).execute()
        
        return {"session": response.data[0]}
    except Exception as e:
        logger.error(f"Session creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions")
async def get_sessions(access_token: str):
    """Get all chat sessions for authenticated user"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        user = verify_token(access_token)
        
        # Get user's chat sessions
        response = supabase.table("chat_sessions")\
            .select("*")\
            .eq("user_id", user.id)\
            .order("updated_at", desc=True)\
            .execute()
        
        return {"sessions": response.data}
    except Exception as e:
        logger.error(f"Get sessions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, access_token: str):
    """Get all messages for a specific session"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        user = verify_token(access_token)
        
        # Get session messages
        response = supabase.table("chat_messages")\
            .select("*")\
            .eq("session_id", session_id)\
            .eq("user_id", user.id)\
            .order("created_at", desc=False)\
            .execute()
        
        return {"messages": response.data}
    except Exception as e:
        logger.error(f"Get messages error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_ai_response(message: str, history: Optional[List[dict]] = None):
    """Internal helper to call OpenAI/OpenRouter"""
    try:
        # Check if API key is set
        if not openrouter_api_key:
            return {"response": "AI Error: OpenRouter API key not configured on Railway server. Please set OPENROUTER_API_KEY in Railway Settings > Variables.", "error": True}

        # Use provided history or start new
        messages = history if history else []
        messages.append({"role": "user", "content": message})
            
        # Call OpenRouter API FAST
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=messages,
            max_tokens=200,  # Shorter for faster voice responses
            temperature=0.7
        )
        
        return {"response": response.choices[0].message.content}
    except Exception as e:
        logger.error(f"AI Response Error: {e}")
        return {"response": f"AI Error: {str(e)}", "error": True}

@app.post("/chat/auth")
async def chat_with_auth(chat_request: ChatRequestAuth):
    """Authenticated chat - loads history from Supabase + background save"""
    try:
        # Load history from Supabase if session_id is provided
        history = []
        if supabase and chat_request.session_id:
            try:
                # verify user first
                user = verify_token(chat_request.access_token)
                
                # Get last 10 messages for this session
                history_resp = supabase.table("chat_messages")\
                    .select("role, content")\
                    .eq("session_id", chat_request.session_id)\
                    .eq("user_id", user.id)\
                    .order("created_at", desc=True)\
                    .limit(10)\
                    .execute()
                
                # Reverse to get chronological order
                raw_history = history_resp.data[::-1]
                history = [{"role": m["role"], "content": m["content"]} for m in raw_history]
                logger.info(f"Loaded {len(history)} messages from history for session {chat_request.session_id}")
            except Exception as e:
                logger.warning(f"Failed to load chat history: {e}")
        
        # Get response using history
        result = await get_ai_response(chat_request.message, history=history)
        
        # Background save to Supabase
        if supabase:
            async def save_to_supabase():
                try:
                    user = verify_token(chat_request.access_token)
                    user_supabase = create_client(supabase_url, supabase_key)
                    user_supabase.postgrest.auth(chat_request.access_token)
                    
                    # Create or use existing session
                    session_id = chat_request.session_id
                    if not session_id:
                        session_response = user_supabase.table("chat_sessions").insert({
                            "user_id": user.id,
                            "title": chat_request.message[:50] + "..."
                        }).execute()
                        session_id = session_response.data[0]["id"]
                    
                    # Save messages
                    user_supabase.table("chat_messages").insert([
                        {"session_id": session_id, "user_id": user.id, "role": "user", "content": chat_request.message},
                        {"session_id": session_id, "user_id": user.id, "role": "assistant", "content": result["response"]}
                    ]).execute()
                    
                    logger.info(f"Background save completed for session {session_id}")
                except Exception as e:
                    logger.error(f"Background Supabase save error: {e}")
            
            # Fire and forget - don't wait!
            asyncio.create_task(save_to_supabase())
        
        # Add session_id to result for client to save
        if chat_request.session_id:
            result["session_id"] = chat_request.session_id
        
        return result
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Authenticated chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """ULTRA-FAST chat - unauthenticated"""
    return await get_ai_response(request.message)

@app.post("/weather")
async def weather_endpoint(request: WeatherRequest):
    try:
        if not weather_api_key:
            return {"error": "Weather API key not configured on server", "city": request.city, "temperature": "N/A", "condition": "Missing API Key"}
            
        url = f'http://api.weatherapi.com/v1/current.json?key={weather_api_key}&q={request.city}&aqi=no'
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "city": data['location']['name'],
                "temperature": data['current']['temp_c'],
                "condition": data['current']['condition']['text']
            }
        else:
            return {"error": f"Failed to fetch weather data: {resp.status_code}", "city": request.city, "temperature": "N/A", "condition": "Error"}
    except Exception as e:
        logger.error(f"Weather error: {e}")
        return {"error": str(e), "city": request.city, "temperature": "N/A", "condition": "Error"}

@app.get("/news")
async def news_endpoint():
    try:
        # Using NewsData.io API (correct one for user's key)
        url = f"https://newsdata.io/api/1/news?apikey={news_api_key}&country=us&language=en"
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            news_items = []
            for article in data.get('results', [])[:5]:
                news_items.append({
                    "title": article.get('title', ''),
                    "description": article.get('description', ''),
                    "link": article.get('link', ''),
                    "pubDate": article.get('pubDate', '')
                })
            return {"news": news_items, "count": len(news_items)}
        else:
            logger.error(f"News API error: {resp.status_code} - {resp.text}")
            return {"news": [], "count": 0, "error": f"Failed to retrieve news: {resp.status_code}"}
    except Exception as e:
        logger.error(f"News error: {str(e)}")
        return {"news": [], "count": 0, "error": str(e)}

@app.get("/cricket/matches")
async def cricket_endpoint():
    try:
        if not cricket_api_key:
            return {"matches": [], "count": 0, "error": "Cricket API key not configured"}
            
        url = f"https://api.cricketdata.org/v1/currentMatches?apikey={cricket_api_key}"
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            matches = []
            # Extract relevant info for the UI
            for match in data.get('data', [])[:5]:
                matches.append({
                    "id": match.get("id"),
                    "name": match.get("name"),
                    "status": match.get("status"),
                    "venue": match.get("venue"),
                    "teams": [match.get("teamInfo", [{}])[0].get("name", "Team 1"), 
                             match.get("teamInfo", [{}])[1].get("name", "Team 2")] if len(match.get("teamInfo", [])) > 1 else ["Unknown", "Unknown"],
                    "score": match.get("score", [])
                })
            return {"matches": matches, "count": len(matches)}
        else:
            return {"matches": [], "count": 0, "error": f"Cricket API error: {resp.status_code}"}
    except Exception as e:
        print(f"Cricket Error: {e}")
        return {"matches": [], "count": 0, "error": str(e)}

@app.get("/gmail")
async def gmail_endpoint(max_results: int = 10, query: str = ""):
    """Get Gmail emails - supports filters like 'is:unread' or 'from:someone@email.com'"""
    try:
        logger.info(f"Gmail request: max_results={max_results}, query={query}")
        result = read_gmail_emails(max_results=max_results, query=query)
        return result
    except Exception as e:
        logger.error(f"Gmail endpoint error: {e}")
        return {"emails": [], "count": 0, "error": str(e)}

@app.post("/youtube/search")
async def youtube_search(request: YoutubeRequest):
    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": request.query,
            "type": "video",
            "key": youtube_api_key,
            "maxResults": 5
        }
        resp = requests.get(url, params=params)
        if resp.status_code == 200:
            data = resp.json()
            videos = []
            for item in data.get("items", []):
                videos.append({
                    "title": item["snippet"]["title"],
                    "videoId": item["id"]["videoId"],
                    "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    "thumbnail": item["snippet"]["thumbnails"]["default"]["url"]
                })
            return {"videos": videos}
        else:
            return {"videos": [], "error": f"YouTube API error: {resp.status_code}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/youtube/play")
async def youtube_play(request: YoutubeRequest):
    """Play YouTube video - returns same as search for now"""
    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": request.query,
            "type": "video",
            "key": youtube_api_key,
            "maxResults": 1
        }
        resp = requests.get(url, params=params)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("items"):
                item = data["items"][0]
                video = {
                    "title": item["snippet"]["title"],
                    "videoId": item["id"]["videoId"],
                    "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    "thumbnail": item["snippet"]["thumbnails"]["default"]["url"]
                }
                return {"video": video, "message": f"Playing: {video['title']}"}
            return {"error": "No video found"}
        else:
            return {"error": f"YouTube API error: {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/tts")
async def tts_endpoint(request: TTSRequest):
    try:
        # Professional male voice: en-US-GuyNeural
        voice = "en-US-GuyNeural" if request.language == "en" else "hi-IN-MadhurNeural"
        
        # Clean text for TTS
        clean_text = request.message.replace("*", "").replace("#", "").strip()
        
        communicate = edge_tts.Communicate(clean_text, voice)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            await communicate.save(tmp_file.name)
            tmp_path = tmp_file.name
            
        with open(tmp_path, "rb") as f:
            audio_data = f.read()
            
        os.unlink(tmp_path)  # Cleanup
        
        return Response(content=audio_data, media_type="audio/mpeg")
    except Exception as e:
        print(f"TTS Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/time")
async def time_endpoint():
    now = datetime.datetime.now()
    return {
        "time": now.strftime("%H:%M"),
        "date": now.strftime("%Y-%m-%d"),
        "day": now.strftime("%A"),
        "greeting": "Good Morning" if now.hour < 12 else "Good Afternoon" if now.hour < 17 else "Good Evening"
    }

# Serve original web-ui.html (full-featured version)
@app.get("/web-ui.html")
async def serve_original_ui():
    web_ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web-ui.html")
    if os.path.exists(web_ui_path):
        return FileResponse(web_ui_path)
    raise HTTPException(status_code=404, detail=f"Original UI not found at {web_ui_path}")

# Serve React static files (if built)
build_path = os.path.join(os.path.dirname(__file__), "jarvis-web-ui", "build")
if os.path.exists(build_path):
    app.mount("/static", StaticFiles(directory=os.path.join(build_path, "static")), name="static")
    
    @app.get("/{full_path:path}")
    async def serve_react(request: Request, full_path: str):
        # Don't intercept API routes and original UI
        if full_path.startswith("api/") or full_path in ["chat", "weather", "news", "youtube/search", "tts", "time", "health", "web-ui.html"]:
            raise HTTPException(status_code=404)
        
        file_path = os.path.join(build_path, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(build_path, "index.html"))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
