from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel


class PartItem(BaseModel):
    name: str
    watched: bool = False


class WatchlistAdd(BaseModel):
    title: str
    category: str = "movie"
    status: str = "to_watch"
    rating: Optional[float] = None
    notes: Optional[str] = None
    imageUrl: Optional[str] = None
    year: Optional[str] = None
    subscribeNews: bool = False
    parts: Optional[List[PartItem]] = None


class WatchlistUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    rating: Optional[float] = None
    notes: Optional[str] = None
    imageUrl: Optional[str] = None
    year: Optional[str] = None
    subscribeNews: Optional[bool] = None
    parts: Optional[List[PartItem]] = None
