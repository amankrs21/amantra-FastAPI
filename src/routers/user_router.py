from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends, status

# local imports
from src.dependencies import get_user_service
from src.middleware.auth import get_current_user
from src.services.user_service import UserService
from src.repository.user_repository import UserRepoError
from src.models.user import UpdateUserRequest, ChangePasswordRequest, MessageResponse


user_route = APIRouter()


@user_route.get("/fetch", status_code=status.HTTP_200_OK)
async def fetch_user(
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> dict:
    try:
        return await service.fetch_user(current_user["id"])
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@user_route.patch("/update", status_code=status.HTTP_200_OK)
async def update_user(
    body: UpdateUserRequest,
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> MessageResponse:
    try:
        return await service.update_user(current_user["id"], body.model_dump())
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@user_route.patch("/changePassword", status_code=status.HTTP_200_OK)
async def change_password(
    body: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> MessageResponse:
    try:
        return await service.change_password(current_user["id"], body.oldPassword, body.newPassword)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@user_route.delete("/deactivate", status_code=status.HTTP_200_OK)
async def deactivate_user(
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> MessageResponse:
    try:
        return await service.deactivate_user(current_user["id"])
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
