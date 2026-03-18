from __future__ import annotations

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


# ── Request Models ──────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    dateOfBirth: Optional[str] = None
    weatherCity: Optional[str] = None


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
    name: Optional[str] = None
    dateOfBirth: Optional[str] = None
    weatherCity: Optional[str] = None
    profilePicture: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    oldPassword: str
    newPassword: str


# ── Response Models ─────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    dateOfBirth: Optional[str] = None
    weatherCity: Optional[str] = None
    avatarUrl: Optional[str] = None
    textVerify: Optional[str] = None
    isVerified: bool = False
    createdAt: Optional[datetime] = None


class AuthResponse(BaseModel):
    token: Optional[str] = None
    message: Optional[str] = None
    user: Optional[UserResponse] = None
    isKeySet: Optional[bool] = None


class MessageResponse(BaseModel):
    message: str


# ── DB Model ────────────────────────────────────────────────────────────────

class UserInDB(BaseModel):
    email: str
    password: Optional[str] = None
    name: str
    dateOfBirth: Optional[str] = None
    weatherCity: Optional[str] = None
    avatarUrl: Optional[str] = None
    textVerify: Optional[str] = None
    isVerified: bool = False
    verificationOTP: Optional[str] = None
    otpExpiresAt: Optional[datetime] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
