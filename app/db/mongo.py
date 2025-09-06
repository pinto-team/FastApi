from motor.motor_asyncio import AsyncIOMotorClient
from bson.codec_options import CodecOptions
from bson.binary import UuidRepresentation
from app.config import get_settings

settings = get_settings()

client = AsyncIOMotorClient(
    settings.mongo_url,
    serverSelectionTimeoutMS=5000,
    uuidRepresentation="standard",
)

db = client.get_database(
    settings.mongo_db,
    codec_options=CodecOptions(uuid_representation=UuidRepresentation.STANDARD),
)

__all__ = ["db"]
