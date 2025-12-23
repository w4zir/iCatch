"""Configuration settings for Sentinel-MAS."""
import os
from dotenv import load_dotenv

load_dotenv()

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192")

# Performance Settings
TIMEOUT_SECONDS = float(os.getenv("TIMEOUT_SECONDS", "3.0"))
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "1000"))

# Dataset Configuration
DATASET_PATH = os.getenv("DATASET_PATH", "data/amazon_fdb.csv")
DATASET_URL = os.getenv(
    "DATASET_URL",
    "https://raw.githubusercontent.com/amazon-science/fraud-dataset-benchmark/main/data/train.csv"
)

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Validation
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable must be set")

