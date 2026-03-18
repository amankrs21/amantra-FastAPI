from __future__ import annotations

from datetime import UTC, datetime

from bson import ObjectId

from src.helpers.response_helper import compute_watchlist_status, serialize_document

# local imports
from src.models.user import MessageResponse
from src.repository.watchlist_repository import WatchlistRepository


class WatchlistService:
    def __init__(self, watchlist_repo: WatchlistRepository) -> None:
        self._repo = watchlist_repo

    async def fetch_watchlist(self, user_id: str) -> list[dict]:
        items = await self._repo.find_by_user(user_id)
        return [serialize_document(item) for item in items]

    async def add_item(self, user_id: str, data: dict) -> dict:
        now = datetime.now(UTC)
        parts_data = [p.model_dump() for p in data.pop("parts")] if data.get("parts") else None
        status = data.get("status", "to_watch")
        auto_status = compute_watchlist_status(parts_data)
        if auto_status is not None:
            status = auto_status
        doc = {
            **data,
            "status": status,
            "parts": parts_data,
            "createdBy": ObjectId(user_id),
            "createdAt": now,
            "updatedAt": now,
        }
        item_id = await self._repo.create(doc)
        return {"message": "Added to watchlist", "_id": item_id}

    async def update_item(self, item_id: str, user_id: str, data: dict) -> MessageResponse:
        existing = await self._repo.find_one(item_id, user_id)
        if not existing:
            raise ValueError("Item not found")
        updates = {k: v for k, v in data.items() if v is not None}
        if "parts" in updates:
            auto_status = compute_watchlist_status(updates["parts"])
            if auto_status is not None:
                updates["status"] = auto_status
        updates["updatedAt"] = datetime.now(UTC)
        await self._repo.update(item_id, user_id, updates)
        return MessageResponse(message="Watchlist item updated")

    async def delete_item(self, item_id: str, user_id: str) -> MessageResponse:
        deleted = await self._repo.delete(item_id, user_id)
        if deleted == 0:
            raise ValueError("Item not found")
        return MessageResponse(message="Removed from watchlist")

    async def get_subscribed(self, user_id: str) -> list[dict]:
        items = await self._repo.get_subscribed_by_user(user_id)
        return [serialize_document(item) for item in items]
