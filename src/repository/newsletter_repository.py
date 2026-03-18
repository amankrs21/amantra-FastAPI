from __future__ import annotations

# local imports
from src.database import get_db


class NewsletterRepoError(RuntimeError):
    """Custom exception for newsletter repository errors."""


class NewsletterRepository:
    def __init__(self) -> None:
        self._db = get_db()
        self._cache = self._db.newsletter_cache

    async def get_cache(self, cache_key: str) -> dict | None:
        return await self._cache.find_one({"_id": cache_key})

    async def set_cache(self, cache_key: str, data: dict) -> None:
        data["_id"] = cache_key
        await self._cache.replace_one({"_id": cache_key}, data, upsert=True)

    async def delete_user_cache(self, user_id: str) -> None:
        await self._cache.delete_one({"_id": f"watchlist_news:{user_id}"})
