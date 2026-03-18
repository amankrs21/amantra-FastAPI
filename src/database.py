from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

# local imports
from src.config import config

_db: AsyncIOMotorDatabase | None = None
_client: AsyncIOMotorClient | None = None


def get_db():
    return _db


async def connect_db():
    global _client, _db
    _client = AsyncIOMotorClient(config.MONGO_URL)
    # Try to get default database from URI, fallback to explicit name
    try:
        _db = _client.get_default_database()
    except Exception:
        _db = _client["AmantraDB"]


async def close_db():
    global _client
    if _client:
        _client.close()
        _client = None
