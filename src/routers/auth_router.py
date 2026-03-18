from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends, status

# local imports
from src.dependencies import get_auth_service
from src.middleware.auth import get_current_user
from src.services.auth_service import AuthService
from src.repository.user_repository import UserRepoError
from src.models.user import (
    LoginRequest, RegisterRequest, VerifyOTPRequest, ResendOTPRequest, ForgotPasswordRequest,
    ResetPasswordRequest, GoogleAuthRequest, AuthResponse, MessageResponse, UserResponse,
)


auth_route = APIRouter()


@auth_route.post("/login", status_code=status.HTTP_200_OK)
async def login(
    request: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        return await service.user_login(request.email, request.password)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(pe))
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@auth_route.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    try:
        return await service.user_register(
            name=request.name,
            email=request.email,
            password=request.password,
            dateOfBirth=request.dateOfBirth,
            weatherCity=request.weatherCity,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@auth_route.post("/verify", status_code=status.HTTP_200_OK)
async def verify_otp(
    request: VerifyOTPRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        return await service.verify_otp(request.email, request.otp)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@auth_route.post("/resend-otp", status_code=status.HTTP_200_OK)
async def resend_otp(
    request: ResendOTPRequest,
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    try:
        return await service.resend_otp(request.email)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@auth_route.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request: ForgotPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    try:
        return await service.forgot_password(request.email)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@auth_route.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request: ResetPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    try:
        return await service.reset_password(request.email, request.otp, request.password)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@auth_route.post("/google", status_code=status.HTTP_200_OK)
async def google_auth(
    request: GoogleAuthRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        return await service.google_auth(request.idToken)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@auth_route.get("/me", status_code=status.HTTP_200_OK)
async def me(
    current_user: dict = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    try:
        return await service.get_current_user(current_user["id"])
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
