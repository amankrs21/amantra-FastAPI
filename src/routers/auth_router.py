from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

# local imports
from src.config import config
from src.dependencies import get_auth_service
from src.middleware.auth import get_current_user
from src.models.user import (
    AuthResponse,
    ForgotPasswordRequest,
    GoogleAuthRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResendOTPRequest,
    ResetPasswordRequest,
    VerifyOTPRequest,
)
from src.repository.user_repository import UserRepoError
from src.services.auth_service import AuthService

auth_route = APIRouter()


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    samesite = config.COOKIE_SAMESITE.lower() if config.COOKIE_SAMESITE else "lax"
    response.set_cookie(
        key=config.REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=config.COOKIE_SECURE,
        samesite=samesite,
        max_age=config.REFRESH_TOKEN_EXPIRES_HOURS * 60 * 60,
        path="/",
    )


@auth_route.post("/login", status_code=status.HTTP_200_OK)
async def login(
    request: LoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        auth_response, refresh_token = await service.user_login(request.email, request.password)
        _set_refresh_cookie(response, refresh_token)
        return auth_response
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(pe)) from pe
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure)) from ure
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure)) from ure
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@auth_route.post("/verify", status_code=status.HTTP_200_OK)
async def verify_otp(
    request: VerifyOTPRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        auth_response, refresh_token = await service.verify_otp(request.email, request.otp)
        _set_refresh_cookie(response, refresh_token)
        return auth_response
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure)) from ure
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@auth_route.post("/resend-otp", status_code=status.HTTP_200_OK)
async def resend_otp(
    request: ResendOTPRequest,
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    try:
        return await service.resend_otp(request.email)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure)) from ure
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@auth_route.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request: ForgotPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    try:
        return await service.forgot_password(request.email)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure)) from ure
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@auth_route.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request: ResetPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    try:
        return await service.reset_password(request.email, request.otp, request.password)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure)) from ure
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@auth_route.post("/google", status_code=status.HTTP_200_OK)
async def google_auth(
    request: GoogleAuthRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        auth_response, refresh_token = await service.google_auth(request.idToken)
        _set_refresh_cookie(response, refresh_token)
        return auth_response
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure)) from ure
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@auth_route.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh_token(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        refresh_token = request.cookies.get(config.REFRESH_TOKEN_COOKIE_NAME)
        if not refresh_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
        auth_response, new_refresh_token = await service.refresh_tokens(refresh_token)
        _set_refresh_cookie(response, new_refresh_token)
        return auth_response
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(pe)) from pe
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure)) from ure
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@auth_route.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    response: Response,
    current_user: dict = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    try:
        await service.logout(current_user["id"])
        samesite = config.COOKIE_SAMESITE.lower() if config.COOKIE_SAMESITE else "lax"
        response.delete_cookie(
            key=config.REFRESH_TOKEN_COOKIE_NAME,
            path="/",
            samesite=samesite,
            secure=config.COOKIE_SECURE,
        )
        return MessageResponse(message="Logged out")
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(pe)) from pe
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure)) from ure
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
