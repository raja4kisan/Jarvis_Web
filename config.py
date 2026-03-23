import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Azure OpenAI Configuration
apikey = os.getenv("AZURE_OPENAI_API_KEY", "")
api_base = os.getenv("AZURE_OPENAI_ENDPOINT", "https://bhanu-mmjcqyw0-eastus2.openai.azure.com/")
api_type = "azure"
api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5.2-bhanu-model")

# YouTube Data API Key
youtube_api_key = os.getenv("YOUTUBE_API_KEY", "")

# Weather API Key (Get free key from: https://www.weatherapi.com/)
weather_api_key = os.getenv("WEATHER_API_KEY", "")

# News API Key (Get free key from: https://newsdata.io/)
news_api_key = os.getenv("NEWS_API_KEY", "")

# DeepSeek API Key
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")

# OpenRouter API Key
openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")

# Cricket API Key (cricketdata.org)
cricket_api_key = os.getenv("CRICKET_API_KEY", "")

# Supabase Configuration
supabase_url = os.getenv("SUPABASE_URL", "")
supabase_key = os.getenv("SUPABASE_KEY", "")
supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY", "")