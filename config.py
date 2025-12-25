"""Configuration settings for Sentinel-MAS."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def resolve_data_path(path: str) -> str:
    """
    Resolve @data/ alias to actual data directory path.
    
    Args:
        path: Path string that may contain @data/ alias
        
    Returns:
        Resolved path string
    """
    if path.startswith("@data/"):
        # Get project root (parent of this file's directory)
        project_root = Path(__file__).parent
        # Replace @data/ with actual data directory path
        resolved = str(project_root / "data" / path[6:])  # Remove "@data/" prefix
        return resolved
    return path


# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
USE_GROQ_API = os.getenv("USE_GROQ_API", "true").lower() in ("true", "1", "yes")

# Performance Settings
TIMEOUT_SECONDS = float(os.getenv("TIMEOUT_SECONDS", "3.0"))
BATCH_TIMEOUT_SECONDS = float(os.getenv("BATCH_TIMEOUT_SECONDS", "15.0"))
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "1000"))
MAX_CONCURRENT_GROQ_REQUESTS = int(os.getenv("MAX_CONCURRENT_GROQ_REQUESTS", "10"))  # Limit concurrent Groq API calls to avoid rate limits

# IEEE Fraud Detection Dataset Configuration
IEEE_TRANSACTION_PATH = resolve_data_path(
    os.getenv("IEEE_TRANSACTION_PATH", "@data/ieee-fraud-detection/train_transaction.csv")
)
IEEE_IDENTITY_PATH = resolve_data_path(
    os.getenv("IEEE_IDENTITY_PATH", "@data/ieee-fraud-detection/train_identity.csv")
)

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Trace Logging Configuration
ENABLE_TRACE_LOGGING = os.getenv("ENABLE_TRACE_LOGGING", "false").lower() in ("true", "1", "yes")
TRACE_LOG_FILE = os.getenv("TRACE_LOG_FILE", "agent_traces.log")
TRACE_LOG_CONSOLE = os.getenv("TRACE_LOG_CONSOLE", "false").lower() in ("true", "1", "yes")

# Validation
if USE_GROQ_API and not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable must be set when USE_GROQ_API is enabled")

