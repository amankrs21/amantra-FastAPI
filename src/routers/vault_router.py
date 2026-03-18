from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends, status

# local imports
from src.dependencies import get_vault_service
from src.middleware.auth import verify_encryption_key
from src.models.user import MessageResponse
from src.services.vault_service import VaultService
from src.repository.vault_repository import VaultRepoError
from src.models.vault import VaultFetchRequest, VaultAddRequest, VaultUpdateRequest, VaultDecryptRequest


vault_route = APIRouter()


@vault_route.post("/fetch", status_code=status.HTTP_200_OK)
async def fetch_vaults(
    body: VaultFetchRequest,
    current_user: dict = Depends(verify_encryption_key),
    service: VaultService = Depends(get_vault_service),
) -> list[dict]:
    try:
        return await service.fetch_vaults(current_user["id"], body.offSet, body.pageSize)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except VaultRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@vault_route.post("/add", status_code=status.HTTP_200_OK)
async def add_vault(
    body: VaultAddRequest,
    current_user: dict = Depends(verify_encryption_key),
    service: VaultService = Depends(get_vault_service),
) -> dict:
    try:
        return await service.add_vault(current_user["id"], body.title, body.username, body.password, body.key)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except VaultRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@vault_route.patch("/update", status_code=status.HTTP_200_OK)
async def update_vault(
    body: VaultUpdateRequest,
    current_user: dict = Depends(verify_encryption_key),
    service: VaultService = Depends(get_vault_service),
) -> MessageResponse:
    try:
        return await service.update_vault(body.id, current_user["id"], body.title, body.username, body.password, body.key)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except VaultRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@vault_route.delete("/delete/{vault_id}", status_code=status.HTTP_200_OK)
async def delete_vault(
    vault_id: str,
    current_user: dict = Depends(verify_encryption_key),
    service: VaultService = Depends(get_vault_service),
) -> MessageResponse:
    try:
        return await service.delete_vault(vault_id, current_user["id"])
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except VaultRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@vault_route.post("/{vault_id}", status_code=status.HTTP_200_OK)
async def decrypt_vault(
    vault_id: str,
    body: VaultDecryptRequest,
    current_user: dict = Depends(verify_encryption_key),
    service: VaultService = Depends(get_vault_service),
) -> dict:
    try:
        return await service.decrypt_vault(vault_id, current_user["id"], body.key)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except VaultRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
