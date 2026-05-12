import os
from dotenv import load_dotenv

load_dotenv()


class Config:

    # Flask
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "supersecretkey"
    )

    # Azure Storage
    AZURE_CONNECTION_STRING = os.getenv(
        "AZURE_CONNECTION_STRING"
    )

    CONTAINER_NAME = os.getenv(
        "CONTAINER_NAME",
        "files"
    )

    # Supabase
    SUPABASE_URL = os.getenv(
        "SUPABASE_URL"
    )

    SUPABASE_KEY = os.getenv(
        "SUPABASE_KEY"
    )

    SUPABASE_SERVICE_KEY = os.getenv(
        "SUPABASE_SERVICE_KEY"
    )

    # Google Gemini
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # Security
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB limit