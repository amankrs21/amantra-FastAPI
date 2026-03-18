from __future__ import annotations

from datetime import UTC, datetime

from bson import ObjectId

from src.helpers.cipher import decrypt, encrypt

# local imports
from src.models.user import MessageResponse
from src.repository.journal_repository import JournalRepository


class JournalService:
    def __init__(self, journal_repo: JournalRepository) -> None:
        self._repo = journal_repo

    async def fetch_journals(self, user_id: str) -> list[dict]:
        journals = await self._repo.find_by_user(user_id)
        return [
            {
                "_id": str(j["_id"]),
                "title": j.get("title"),
                "content": None,
                "updatedAt": j.get("updatedAt"),
            }
            for j in journals
        ]

    async def add_journal(self, user_id: str, title: str, content: str, key: str) -> dict:
        encrypted_content = encrypt(content, key)
        doc = {
            "title": title,
            "content": encrypted_content,
            "updatedAt": datetime.now(UTC),
            "createdBy": ObjectId(user_id),
        }
        journal_id = await self._repo.create(doc)
        return {"message": "Journal added", "_id": journal_id}

    async def update_journal(
        self, journal_id: str, user_id: str, title: str, content: str, key: str
    ) -> MessageResponse:
        encrypted_content = encrypt(content, key)
        matched = await self._repo.update(
            journal_id,
            user_id,
            {
                "title": title,
                "content": encrypted_content,
                "updatedAt": datetime.now(UTC),
            },
        )
        if matched == 0:
            raise ValueError("Journal not found")
        return MessageResponse(message="Journal updated")

    async def delete_journal(self, journal_id: str, user_id: str) -> MessageResponse:
        deleted = await self._repo.delete(journal_id, user_id)
        if deleted == 0:
            raise ValueError("Journal not found")
        return MessageResponse(message="Journal deleted")

    async def decrypt_journal(self, journal_id: str, user_id: str, key: str) -> dict:
        journal = await self._repo.find_one(journal_id, user_id)
        if not journal:
            raise ValueError("Journal not found")
        if not journal.get("content"):
            raise ValueError("No content stored")
        try:
            decrypted = decrypt(journal["content"], key)
        except Exception as exc:
            raise ValueError("Invalid Encryption Key!") from exc
        return {"content": decrypted}
