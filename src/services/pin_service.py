from __future__ import annotations

# local imports
from src.helpers.cipher import encrypt
from src.models.user import MessageResponse
from src.repository.user_repository import UserRepository
from src.repository.vault_repository import VaultRepository
from src.repository.journal_repository import JournalRepository


class PinService:
    def __init__(self, user_repo: UserRepository, vault_repo: VaultRepository, journal_repo: JournalRepository) -> None:
        self._user_repo = user_repo
        self._vault_repo = vault_repo
        self._journal_repo = journal_repo


    async def verify_key(self) -> MessageResponse:
        return MessageResponse(message="Valid Encryption Key!")


    async def set_text(self, user_id: str, key: str) -> MessageResponse:
        encrypted = encrypt("Hey SV, Verify me!", key)
        await self._user_repo.update_user(user_id, {"textVerify": encrypted})
        return MessageResponse(message="Encryption key set")


    async def reset_pin(self, user_id: str) -> MessageResponse:
        await self._user_repo.update_user(user_id, {"textVerify": None})
        await self._journal_repo.nullify_content_by_user(user_id)
        await self._vault_repo.nullify_passwords_by_user(user_id)
        return MessageResponse(message="PIN reset successful")
