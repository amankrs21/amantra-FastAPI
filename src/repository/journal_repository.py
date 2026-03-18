from __future__ import annotations

from bson import ObjectId

# local imports
from src.database import get_db


class JournalRepoError(RuntimeError):
    """Custom exception for journal repository errors."""


class JournalRepository:
    def __init__(self) -> None:
        self._db = get_db()
        self._journals = self._db.journalmodels

    async def find_by_user(self, user_id: str) -> list[dict]:
        cursor = self._journals.find({"createdBy": ObjectId(user_id)}).sort("updatedAt", -1)
        return await cursor.to_list(500)

    async def find_one(self, journal_id: str, user_id: str) -> dict | None:
        return await self._journals.find_one({"_id": ObjectId(journal_id), "createdBy": ObjectId(user_id)})

    async def create(self, doc: dict) -> str:
        result = await self._journals.insert_one(doc)
        return str(result.inserted_id)

    async def update(self, journal_id: str, user_id: str, update: dict) -> int:
        result = await self._journals.update_one(
            {"_id": ObjectId(journal_id), "createdBy": ObjectId(user_id)},
            {"$set": update},
        )
        return result.matched_count

    async def delete(self, journal_id: str, user_id: str) -> int:
        result = await self._journals.delete_one({"_id": ObjectId(journal_id), "createdBy": ObjectId(user_id)})
        return result.deleted_count

    async def delete_many_by_user(self, user_id: str) -> int:
        result = await self._journals.delete_many({"createdBy": ObjectId(user_id)})
        return result.deleted_count

    async def nullify_content_by_user(self, user_id: str) -> None:
        await self._journals.update_many({"createdBy": ObjectId(user_id)}, {"$set": {"content": None}})
