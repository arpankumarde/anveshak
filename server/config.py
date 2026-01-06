"""Configuration management for the application."""
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/anveshak")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "anveshak")

# LangChain/OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", None)  # None uses default OpenAI API
LANGCHAIN_MODEL = os.getenv("LANGCHAIN_MODEL", "google/gemini-2.5-flash-lite-preview-09-2025")
LANGCHAIN_TEMPERATURE = float(os.getenv("LANGCHAIN_TEMPERATURE", "0.1"))

# Processing Configuration
LOG_BATCH_SIZE = int(os.getenv("LOG_BATCH_SIZE", "50"))  # Reduced to prevent timeouts
PROCESSING_INTERVAL = float(os.getenv("PROCESSING_INTERVAL", "5.0"))  # seconds
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))  # seconds for LLM API calls
LLM_BATCH_SIZE = int(os.getenv("LLM_BATCH_SIZE", "10"))  # Process LLM calls in smaller batches

# Severity Thresholds
CRASH_SEVERITY_THRESHOLD = 8
ERROR_SEVERITY_THRESHOLD = 5
WARNING_SEVERITY_THRESHOLD = 3

