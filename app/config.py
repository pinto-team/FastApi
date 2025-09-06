from functools import lru_cache
from pydantic import BaseModel
import os

class Settings(BaseModel):
    project_name: str = "Wholesale Supermarket API"
    debug: bool = True

    # MongoDB
    mongo_url: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    mongo_db: str = os.getenv("MONGO_DB", "mockapi")

@lru_cache
def get_settings() -> Settings:
    return Settings()
