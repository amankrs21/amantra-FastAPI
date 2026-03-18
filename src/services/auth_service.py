from __future__ import annotations

from datetime import datetime, timezone

# local imports
from src.config import config
from src.helpers.auth_helper import AuthHelper
from src.models.user import AuthResponse, UserResponse, MessageResponse
from src.repository.user_repository import UserRepository
from src.services.email_service import EmailService


def _build_user_response(user: dict) -> UserResponse:
    return UserResponse(
        id=str(user["_id"]),
        name=user.get("name", ""),
        email=user.get("email", ""),
        dateOfBirth=user.get("dateOfBirth"),
        weatherCity=user.get("weatherCity"),
        avatarUrl=user.get("avatarUrl"),
        textVerify=user.get("textVerify"),
        isVerified=user.get("isVerified", False),
        createdAt=user.get("createdAt"),
    )


class AuthService:
    def __init__(self, user_repo: UserRepository, email_service: EmailService) -> None:
        self._repo = user_repo
        self._email = email_service
        self._helper = AuthHelper()

    # ── Login ───────────────────────────────────────────────────────────────

    async def user_login(self, email: str, password: str) -> AuthResponse:
        user = await self._repo.get_user_by_email(email)
        if not user or not user.get("password"):
            raise PermissionError("Invalid credentials")
        if not self._helper.verify_password(password, user["password"]):
            raise PermissionError("Invalid credentials")
        if not user.get("isVerified", False):
            raise PermissionError("Please verify your email before logging in")
        token = self._helper.create_access_token({"id": str(user["_id"]), "name": user.get("name")})
        return AuthResponse(
            token=token,
            message="Login successful",
            user=_build_user_response(user),
            isKeySet=user.get("textVerify") is not None,
        )

    # ── Register ────────────────────────────────────────────────────────────

    async def user_register(self, name: str, email: str, password: str, dateOfBirth: str | None = None, weatherCity: str | None = None) -> MessageResponse:
        existing = await self._repo.get_user_by_email(email)
        if existing:
            raise ValueError("Email already registered")
        hashed = self._helper.hash_password(password)
        otp = self._helper.generate_otp()
        otp_expiry = self._helper.get_otp_expiry()
        avatar_url = f"https://api.dicebear.com/9.x/fun-emoji/svg?seed={email}"
        user_doc = {
            "email": email,
            "password": hashed,
            "name": name,
            "dateOfBirth": dateOfBirth,
            "weatherCity": weatherCity,
            "avatarUrl": avatar_url,
            "textVerify": None,
            "isVerified": False,
            "verificationOTP": otp,
            "otpExpiresAt": otp_expiry,
            "createdAt": datetime.now(timezone.utc),
        }
        await self._repo.create_user(user_doc)
        await self._email.send_otp_email(email, otp, purpose="verification")
        return MessageResponse(message="Registration successful. Please check your email for OTP.")

    # ── Verify OTP ──────────────────────────────────────────────────────────

    async def verify_otp(self, email: str, otp: str) -> AuthResponse:
        user = await self._repo.get_user_by_email(email)
        if not user:
            raise ValueError("User not found")
        if user.get("isVerified", False):
            raise ValueError("Email already verified")
        stored_otp = user.get("verificationOTP")
        otp_expires = user.get("otpExpiresAt")
        if not stored_otp or stored_otp != otp:
            raise ValueError("Invalid OTP")
        if otp_expires and datetime.now(timezone.utc) > otp_expires.replace(tzinfo=timezone.utc) if otp_expires.tzinfo is None else otp_expires:
            raise ValueError("OTP has expired")
        await self._repo.update_user(str(user["_id"]), {
            "isVerified": True,
            "verificationOTP": None,
            "otpExpiresAt": None,
        })
        user["isVerified"] = True
        token = self._helper.create_access_token({"id": str(user["_id"]), "name": user.get("name")})
        return AuthResponse(
            token=token,
            message="Email verified successfully",
            user=_build_user_response(user),
            isKeySet=user.get("textVerify") is not None,
        )

    # ── Resend OTP ──────────────────────────────────────────────────────────

    async def resend_otp(self, email: str) -> MessageResponse:
        user = await self._repo.get_user_by_email(email)
        if not user:
            raise ValueError("User not found")
        if user.get("isVerified", False):
            raise ValueError("Email already verified")
        otp = self._helper.generate_otp()
        otp_expiry = self._helper.get_otp_expiry()
        await self._repo.update_user(str(user["_id"]), {
            "verificationOTP": otp,
            "otpExpiresAt": otp_expiry,
        })
        await self._email.send_otp_email(email, otp, purpose="verification")
        return MessageResponse(message="OTP resent successfully")

    # ── Forgot Password ─────────────────────────────────────────────────────

    async def forgot_password(self, email: str) -> MessageResponse:
        user = await self._repo.get_user_by_email(email)
        if not user:
            raise ValueError("User not found")
        otp = self._helper.generate_otp()
        otp_expiry = self._helper.get_otp_expiry()
        await self._repo.update_user(str(user["_id"]), {
            "verificationOTP": otp,
            "otpExpiresAt": otp_expiry,
        })
        await self._email.send_otp_email(email, otp, purpose="password reset")
        return MessageResponse(message="OTP sent to your email")

    # ── Reset Password ───────────────────────────────────────────────────────

    async def reset_password(self, email: str, otp: str, password: str) -> MessageResponse:
        user = await self._repo.get_user_by_email(email)
        if not user:
            raise ValueError("User not found")
        stored_otp = user.get("verificationOTP")
        otp_expires = user.get("otpExpiresAt")
        if not stored_otp or stored_otp != otp:
            raise ValueError("Invalid OTP")
        if otp_expires and datetime.now(timezone.utc) > (otp_expires.replace(tzinfo=timezone.utc) if otp_expires.tzinfo is None else otp_expires):
            raise ValueError("OTP has expired")
        hashed = self._helper.hash_password(password)
        await self._repo.update_user(str(user["_id"]), {
            "password": hashed,
            "verificationOTP": None,
            "otpExpiresAt": None,
        })
        return MessageResponse(message="Password reset successful")

    # ── Google Auth ──────────────────────────────────────────────────────────

    async def google_auth(self, id_token_str: str) -> AuthResponse:
        idinfo = self._helper.verify_google_token(id_token_str, config.google_client_ids)
        email = idinfo["email"]
        user = await self._repo.get_user_by_email(email)
        if not user:
            user_doc = {
                "email": email,
                "password": None,
                "name": idinfo.get("name", ""),
                "dateOfBirth": None,
                "weatherCity": None,
                "avatarUrl": idinfo.get("picture"),
                "textVerify": None,
                "isVerified": True,
                "verificationOTP": None,
                "otpExpiresAt": None,
                "createdAt": datetime.now(timezone.utc),
            }
            user = await self._repo.create_user(user_doc)
        token = self._helper.create_access_token({
            "id": str(user["_id"]),
            "name": user.get("name"),
            "email": user.get("email"),
            "avatarUrl": user.get("avatarUrl"),
        })
        return AuthResponse(
            token=token,
            message="Google authentication successful",
            user=_build_user_response(user),
            isKeySet=user.get("textVerify") is not None,
        )

    # ── Get Current User ─────────────────────────────────────────────────────

    async def get_current_user(self, user_id: str) -> UserResponse:
        user = await self._repo.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return _build_user_response(user)
