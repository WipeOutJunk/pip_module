# config.py
import os
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные из .env файла

class Config:
    OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://172.18.0.2:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", 4000))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "temp")
    ALLOWED_EXTENSIONS = {'pdf'}
    FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True") == "True"
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")  # Новый параметр
    MAX_GENERATION_TIME= int(os.getenv("MAX_GENERATION_TIME",300))

    # OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")  # Если требуется
