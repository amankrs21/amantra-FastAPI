from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

# ── Request Models ──────────────────────────────────────────────────────────


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    dateOfBirth: str | None = None
    weatherCity: str | None = None


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str


class ResendOTPRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    password: str


class GoogleAuthRequest(BaseModel):
    idToken: str


class UpdateUserRequest(BaseModel):
    name: str | None = None
    dateOfBirth: str | None = None
    weatherCity: str | None = None
    profilePicture: str | None = None


class ChangePasswordRequest(BaseModel):
    oldPassword: str
    newPassword: str


# ── Response Models ─────────────────────────────────────────────────────────


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    dateOfBirth: str | None = None
    weatherCity: str | None = None
    avatarUrl: str | None = None
    textVerify: str | None = None
    isVerified: bool = False
    createdAt: datetime | None = None


class AuthResponse(BaseModel):
    token: str | None = None
    message: str | None = None
    user: UserResponse | None = None
    isKeySet: bool | None = None


class MessageResponse(BaseModel):
    message: str


# ── DB Model ────────────────────────────────────────────────────────────────


class UserInDB(BaseModel):
    email: str
    password: str | None = None
    name: str
    dateOfBirth: str | None = None
    weatherCity: str | None = None
    avatarUrl: str | None = None
    textVerify: str | None = None
    isVerified: bool = False
    verificationOTP: str | None = None
    otpExpiresAt: datetime | None = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
