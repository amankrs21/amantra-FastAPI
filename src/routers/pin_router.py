from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends, status

# local imports
from src.dependencies import get_pin_service
from src.middleware.auth import verify_encryption_key
from src.models.user import MessageResponse
from src.services.pin_service import PinService
from src.repository.user_repository import UserRepoError


pin_route = APIRouter()


class SetTextRequest(BaseModel):
    key: str


class VerifyRequest(BaseModel):
    key: str


@pin_route.post("/verify", status_code=status.HTTP_200_OK)
async def verify_pin(
    body: VerifyRequest,
    current_user: dict = Depends(verify_encryption_key),
    service: PinService = Depends(get_pin_service),
) -> MessageResponse:
    try:
        return await service.verify_key()
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@pin_route.post("/setText", status_code=status.HTTP_200_OK)
async def set_text(
    body: SetTextRequest,
    current_user: dict = Depends(verify_encryption_key),
    service: PinService = Depends(get_pin_service),
) -> MessageResponse:
    try:
        return await service.set_text(current_user["id"], body.key)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@pin_route.get("/reset", status_code=status.HTTP_200_OK)
async def reset_pin(
    current_user: dict = Depends(verify_encryption_key),
    service: PinService = Depends(get_pin_service),
) -> MessageResponse:
    try:
        return await service.reset_pin(current_user["id"])
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
