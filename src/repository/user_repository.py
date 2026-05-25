from __future__ import annotations

from bson import ObjectId

# local imports
from src.database import get_db


class UserRepoError(RuntimeError):
    """Custom exception for user repository errors."""


class UserRepository:
    def __init__(self) -> None:
        self._db = get_db()
        self._users = self._db.usermodels

    async def get_user_by_email(self, email: str) -> dict | None:
        return await self._users.find_one({"email": email})

    async def get_user_by_id(self, user_id: str) -> dict | None:
        return await self._users.find_one({"_id": ObjectId(user_id)})

    async def create_user(self, user_doc: dict) -> dict:
        result = await self._users.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        return user_doc

    async def update_user(self, user_id: str, update: dict) -> None:
        await self._users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update},
        )

    async def delete_user(self, user_id: str) -> None:
        await self._users.delete_one({"_id": ObjectId(user_id)})

    async def find_one(self, query: dict) -> dict | None:
        return await self._users.find_one(query)
