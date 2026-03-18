from __future__ import annotations

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    
class LoginResponse(BaseModel):
    token: str
    message: Optional[str] = None
    
    
class UserInDB(BaseModel):
    email: str
    password: Optional[str] = None
    name: str
    dateOfBirth: Optional[str] = None
    secretAnswer: Optional[str] = None
    textVerify: Optional[str] = None
    avatarUrl: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    secretAnswer: Optional[str] = None


class ForgetRequest(BaseModel):
    email: str
    dob: str
    answer: str
    password: str


class GoogleAuthRequest(BaseModel):
    idToken: str
