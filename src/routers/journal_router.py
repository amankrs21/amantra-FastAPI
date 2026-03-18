from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

# local imports
from src.dependencies import get_journal_service
from src.middleware.auth import verify_encryption_key
from src.models.journal import JournalAddRequest, JournalDecryptRequest, JournalUpdateRequest
from src.models.user import MessageResponse
from src.repository.journal_repository import JournalRepoError
from src.services.journal_service import JournalService

journal_route = APIRouter()


@journal_route.get("/fetch", status_code=status.HTTP_200_OK)
async def fetch_journals(
    current_user: dict = Depends(verify_encryption_key),
    service: JournalService = Depends(get_journal_service),
) -> list[dict]:
    try:
        return await service.fetch_journals(current_user["id"])
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except JournalRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure)) from ure
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@journal_route.post("/add", status_code=status.HTTP_200_OK)
async def add_journal(
    body: JournalAddRequest,
    current_user: dict = Depends(verify_encryption_key),
    service: JournalService = Depends(get_journal_service),
) -> dict:
    try:
        return await service.add_journal(current_user["id"], body.title, body.content, body.key)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except JournalRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure)) from ure
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@journal_route.patch("/update", status_code=status.HTTP_200_OK)
async def update_journal(
    body: JournalUpdateRequest,
    current_user: dict = Depends(verify_encryption_key),
    service: JournalService = Depends(get_journal_service),
) -> MessageResponse:
    try:
        return await service.update_journal(body.id, current_user["id"], body.title, body.content, body.key)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except JournalRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure)) from ure
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@journal_route.delete("/delete/{journal_id}", status_code=status.HTTP_200_OK)
async def delete_journal(
    journal_id: str,
    current_user: dict = Depends(verify_encryption_key),
    service: JournalService = Depends(get_journal_service),
) -> MessageResponse:
    try:
        return await service.delete_journal(journal_id, current_user["id"])
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except JournalRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure)) from ure
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@journal_route.post("/{journal_id}", status_code=status.HTTP_200_OK)
async def decrypt_journal(
    journal_id: str,
    body: JournalDecryptRequest,
    current_user: dict = Depends(verify_encryption_key),
    service: JournalService = Depends(get_journal_service),
) -> dict:
    try:
        return await service.decrypt_journal(journal_id, current_user["id"], body.key)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except JournalRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure)) from ure
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
