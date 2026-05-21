from __future__ import annotations

from pydantic import BaseModel


class VaultFetchRequest(BaseModel):
    pageSize: int = 10
    offSet: int = 0


class VaultAddRequest(BaseModel):
    key: str
    title: str
    username: str
    password: str
    category: str | None = None


class VaultUpdateRequest(BaseModel):
    id: str
    key: str
    title: str
    username: str
    password: str
    category: str | None = None


class VaultDecryptRequest(BaseModel):
    key: str
