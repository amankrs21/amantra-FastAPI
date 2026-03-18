from __future__ import annotations

from bson import ObjectId
from typing import Optional

# local imports
from src.database import get_db


class VaultRepoError(RuntimeError):
    """Custom exception for vault repository errors."""


class VaultRepository:
    def __init__(self) -> None:
        self._db = get_db()
        self._vaults = self._db.vaultmodels

    async def find_by_user(self, user_id: str, offset: int = 0, limit: int = 10) -> list[dict]:
        cursor = self._vaults.find({"createdBy": ObjectId(user_id)}).sort("updatedAt", -1).skip(offset).limit(limit)
        return await cursor.to_list(limit)

    async def find_one(self, vault_id: str, user_id: str) -> Optional[dict]:
        return await self._vaults.find_one({"_id": ObjectId(vault_id), "createdBy": ObjectId(user_id)})

    async def create(self, doc: dict) -> str:
        result = await self._vaults.insert_one(doc)
        return str(result.inserted_id)

    async def update(self, vault_id: str, user_id: str, update: dict) -> int:
        result = await self._vaults.update_one(
            {"_id": ObjectId(vault_id), "createdBy": ObjectId(user_id)},
            {"$set": update},
        )
        return result.matched_count

    async def delete(self, vault_id: str, user_id: str) -> int:
        result = await self._vaults.delete_one({"_id": ObjectId(vault_id), "createdBy": ObjectId(user_id)})
        return result.deleted_count

    async def delete_many_by_user(self, user_id: str) -> int:
        result = await self._vaults.delete_many({"createdBy": ObjectId(user_id)})
        return result.deleted_count

    async def nullify_passwords_by_user(self, user_id: str) -> None:
        await self._vaults.update_many({"createdBy": ObjectId(user_id)}, {"$set": {"password": None}})
