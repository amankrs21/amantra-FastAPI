from __future__ import annotations

from bson import ObjectId

# local imports
from src.database import get_db


class WatchlistRepoError(RuntimeError):
    """Custom exception for watchlist repository errors."""


class WatchlistRepository:
    def __init__(self) -> None:
        self._db = get_db()
        self._watchlist = self._db.watchlistmodels

    async def find_by_user(self, user_id: str) -> list[dict]:
        cursor = self._watchlist.find({"createdBy": ObjectId(user_id)}).sort("createdAt", -1)
        return await cursor.to_list(500)

    async def find_one(self, item_id: str, user_id: str) -> dict | None:
        return await self._watchlist.find_one({"_id": ObjectId(item_id), "createdBy": ObjectId(user_id)})

    async def create(self, doc: dict) -> str:
        result = await self._watchlist.insert_one(doc)
        return str(result.inserted_id)

    async def update(self, item_id: str, user_id: str, update: dict) -> int:
        result = await self._watchlist.update_one(
            {"_id": ObjectId(item_id), "createdBy": ObjectId(user_id)},
            {"$set": update},
        )
        return result.matched_count

    async def delete(self, item_id: str, user_id: str) -> int:
        result = await self._watchlist.delete_one({"_id": ObjectId(item_id), "createdBy": ObjectId(user_id)})
        return result.deleted_count

    async def delete_many_by_user(self, user_id: str) -> int:
        result = await self._watchlist.delete_many({"createdBy": ObjectId(user_id)})
        return result.deleted_count

    async def get_subscribed_by_user(self, user_id: str) -> list[dict]:
        cursor = self._watchlist.find({"createdBy": ObjectId(user_id), "subscribeNews": True})
        return await cursor.to_list(100)
