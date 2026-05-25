from __future__ import annotations

from pydantic import BaseModel


class PartItem(BaseModel):
    name: str
    watched: bool = False


class WatchlistAdd(BaseModel):
    title: str
    category: str = "movie"
    status: str = "to_watch"
    rating: float | None = None
    notes: str | None = None
    imageUrl: str | None = None
    year: str | None = None
    subscribeNews: bool = False
    parts: list[PartItem] | None = None


class WatchlistUpdate(BaseModel):
    title: str | None = None
    category: str | None = None
    status: str | None = None
    rating: float | None = None
    notes: str | None = None
    imageUrl: str | None = None
    year: str | None = None
    subscribeNews: bool | None = None
    parts: list[PartItem] | None = None
