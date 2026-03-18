from __future__ import annotations

from src.helpers.auth_helper import AuthHelper

# local imports
from src.helpers.response_helper import build_user_dict
from src.models.user import MessageResponse
from src.repository.journal_repository import JournalRepository
from src.repository.newsletter_repository import NewsletterRepository
from src.repository.user_repository import UserRepository
from src.repository.vault_repository import VaultRepository
from src.repository.watchlist_repository import WatchlistRepository


class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        vault_repo: VaultRepository,
        journal_repo: JournalRepository,
        watchlist_repo: WatchlistRepository,
        newsletter_repo: NewsletterRepository,
    ) -> None:
        self._repo = user_repo
        self._vault_repo = vault_repo
        self._journal_repo = journal_repo
        self._watchlist_repo = watchlist_repo
        self._newsletter_repo = newsletter_repo
        self._helper = AuthHelper()

    async def fetch_user(self, user_id: str) -> dict:
        user = await self._repo.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return build_user_dict(user)

    async def update_user(self, user_id: str, update: dict) -> MessageResponse:
        filtered = {k: v for k, v in update.items() if v is not None}
        if not filtered:
            raise ValueError("Nothing to update")
        await self._repo.update_user(user_id, filtered)
        return MessageResponse(message="User updated")

    async def change_password(self, user_id: str, old_password: str, new_password: str) -> MessageResponse:
        user = await self._repo.get_user_by_id(user_id)
        if not user or not user.get("password"):
            raise ValueError("Cannot change password")
        if not self._helper.verify_password(old_password, user["password"]):
            raise ValueError("Invalid old password")
        hashed = self._helper.hash_password(new_password)
        await self._repo.update_user(user_id, {"password": hashed})
        return MessageResponse(message="Password changed")

    async def deactivate_user(self, user_id: str) -> MessageResponse:
        """Delete user and ALL associated data (vaults, journals, watchlists, newsletter cache)."""
        await self._vault_repo.delete_many_by_user(user_id)
        await self._journal_repo.delete_many_by_user(user_id)
        await self._watchlist_repo.delete_many_by_user(user_id)
        await self._newsletter_repo.delete_user_cache(user_id)
        await self._repo.delete_user(user_id)
        return MessageResponse(message="Account deactivated and all data deleted")
