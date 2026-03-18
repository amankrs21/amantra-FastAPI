from __future__ import annotations

from pydantic import BaseModel


class JournalAddRequest(BaseModel):
    key: str
    title: str
    content: str


class JournalUpdateRequest(BaseModel):
    id: str
    key: str
    title: str
    content: str


class JournalDecryptRequest(BaseModel):
    key: str
