# app/core/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    # --------------------------------------------
    # PROJECT INFO
    # --------------------------------------------
    PROJECT_NAME: str = "Zylos AI Assistant"
    API_V1_STR: str = "/api"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # --------------------------------------------
    # DATABASE MODE
    # Options: sqlite / supabase / firestore
    # --------------------------------------------
    DATABASE_MODE: str = "sqlite"
    DATABASE_URL: str = "sqlite:///app/data/memory.db"

    # --------------------------------------------
    # SUPABASE (Optional)
    # --------------------------------------------
    SUPABASE_URL: str | None = None
    SUPABASE_KEY: str | None = None

    # --------------------------------------------
    # SECURITY
    # --------------------------------------------
    SECRET_KEY: str = "replace-with-strong-secret"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # --------------------------------------------
    # AI MODEL CONFIG
    # --------------------------------------------
    MODEL_CLI_CMD: str = "gpt4all"
    MODEL_PATH: str = "app/models/local_models/phi3.bin"

    # --------------------------------------------
    # OCR / TESSERACT (OPTIONAL)
    # --------------------------------------------
    TESSERACT_CMD: str | None = None

    # --------------------------------------------
    # DEBUG MODE
    # --------------------------------------------
    DEBUG: bool = True

    # --------------------------------------------
    # REDIS (for multi-device sync)
    # --------------------------------------------
    REDIS_URL: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()