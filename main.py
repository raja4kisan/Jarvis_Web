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
from openai import AzureOpenAI
from config import apikey, api_base, api_version, deployment_name, youtube_api_key, weather_api_key, news_api_key, cricket_api_key

app = FastAPI(title="Jarvis AI API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=apikey,
    api_version=api_version,
    azure_endpoint=api_base
)

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

# Global context memory (Simulated for single user, recommend Redis for multi-user)
chat_history = []

@app.get("/")
async def root():
    return {
        "message": "Jarvis AI is running!",
        "status": "online",
        "version": "1.1.0"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    global chat_history
    try:
        # Add user message to history
        chat_history.append({"role": "user", "content": request.message})
        
        # Keep history concise (last 10 exchanges)
        if len(chat_history) > 20:
            chat_history = chat_history[-20:]
            
        # Call Azure OpenAI
        response = client.chat.completions.create(
            model=deployment_name,
            messages=chat_history,
            max_completion_tokens=300,
            temperature=0.9
        )
        
        ai_response = response.choices[0].message.content
        chat_history.append({"role": "assistant", "content": ai_response})
        
        return {"response": ai_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/weather")
async def weather_endpoint(request: WeatherRequest):
    try:
        url = f'http://api.weatherapi.com/v1/current.json?key={weather_api_key}&q={request.city}&aqi=no'
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "city": data['location']['name'],
                "temperature": data['current']['temp_c'],
                "condition": data['current']['condition']['text'],
                "humidity": data['current']['humidity']
            }
        else:
            raise HTTPException(status_code=404, detail="City not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/news")
async def news_endpoint():
    try:
        # Using NewsAPI as per Jarvis.py logic
        url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={news_api_key}"
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            news_items = []
            for article in data.get('articles', [])[:5]:
                news_items.append({
                    "title": article['title'],
                    "description": article.get('description', ''),
                    "link": article.get('url', ''),
                    "pubDate": article.get('publishedAt', '')
                })
            return {"news": news_items, "count": len(news_items)}
        else:
            return {"news": [], "count": 0, "error": "Failed to retrieve news"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

# Serve React static files (if built)
build_path = os.path.join(os.path.dirname(__file__), "jarvis-web-ui", "build")
if os.path.exists(build_path):
    app.mount("/static", StaticFiles(directory=os.path.join(build_path, "static")), name="static")
    
    @app.get("/{full_path:path}")
    async def serve_react(request: Request, full_path: str):
        # Don't intercept API routes
        if full_path.startswith("api/") or full_path in ["chat", "weather", "news", "youtube/search", "tts", "time", "health"]:
            raise HTTPException(status_code=404)
        
        file_path = os.path.join(build_path, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(build_path, "index.html"))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
