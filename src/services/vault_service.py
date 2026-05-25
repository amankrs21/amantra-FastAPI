from __future__ import annotations

import base64
from datetime import UTC, datetime

from bson import ObjectId

from src.helpers.cipher import decrypt, encrypt

# local imports
from src.models.user import MessageResponse
from src.repository.vault_repository import VaultRepository


class VaultService:
    def __init__(self, vault_repo: VaultRepository) -> None:
        self._repo = vault_repo

    async def fetch_vaults(self, user_id: str, offset: int = 0, page_size: int = 10) -> list[dict]:
        vaults = await self._repo.find_by_user(user_id, offset, page_size)
        return [
            {
                "_id": str(v["_id"]),
                "title": v.get("title"),
                "username": v.get("username"),
                "password": None,
                "category": v.get("category"),
                "updatedAt": v.get("updatedAt"),
            }
            for v in vaults
        ]

    async def add_vault(self, user_id: str, title: str, username: str, password: str, key: str, category: str | None = None) -> dict:
        encrypted_pw = encrypt(password, key)
        doc = {
            "title": title,
            "username": username,
            "password": encrypted_pw,
            "category": category,
            "updatedAt": datetime.now(UTC),
            "createdBy": ObjectId(user_id),
        }
        vault_id = await self._repo.create(doc)
        return {"message": "Vault added", "_id": vault_id}

    async def update_vault(
        self, vault_id: str, user_id: str, title: str, username: str, password: str, key: str, category: str | None = None
    ) -> MessageResponse:
        encrypted_pw = encrypt(password, key)
        matched = await self._repo.update(
            vault_id,
            user_id,
            {
                "title": title,
                "username": username,
                "password": encrypted_pw,
                "category": category,
                "updatedAt": datetime.now(UTC),
            },
        )
        if matched == 0:
            raise ValueError("Vault not found")
        return MessageResponse(message="Vault updated")

    async def delete_vault(self, vault_id: str, user_id: str) -> MessageResponse:
        deleted = await self._repo.delete(vault_id, user_id)
        if deleted == 0:
            raise ValueError("Vault not found")
        return MessageResponse(message="Vault deleted")

    async def decrypt_vault(self, vault_id: str, user_id: str, key: str) -> dict:
        vault = await self._repo.find_one(vault_id, user_id)
        if not vault:
            raise ValueError("Vault not found")
        if not vault.get("password"):
            raise ValueError("No password stored")
        try:
            decrypted = decrypt(vault["password"], key)
        except Exception as exc:
            raise ValueError("Invalid Encryption Key!") from exc
        encoded = base64.b64encode(decrypted.encode("utf-8")).decode("utf-8")
        return {"password": encoded}
