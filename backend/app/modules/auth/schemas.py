# -*- coding: utf-8 -*-
"""
認證相關的 Pydantic Schemas
定義 API 請求和響應的資料結構
"""
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


# ===========================================
# 登入相關 Schemas
# ===========================================

class LoginRequest(BaseModel):
    """登入請求"""
    username: str = Field(..., description="使用者名稱或電子郵件", min_length=3, max_length=255)
    password: str = Field(..., description="密碼", min_length=6, max_length=100)

    @field_validator('username', 'password')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """清除前後空白字符"""
        return v.strip() if v else v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "admin",
                    "password": "admin123"
                }
            ]
        }
    }


class TokenResponse(BaseModel):
    """Token 響應"""
    access_token: str = Field(..., description="訪問令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌類型")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer"
                }
            ]
        }
    }


class LoginResponse(BaseModel):
    """登入響應（使用者資訊，tokens 在 httpOnly cookie 中）"""
    user: "UserInfo" = Field(..., description="使用者資訊")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user": {
                        "id": 1,
                        "username": "admin",
                        "email": "admin@example.com",
                        "full_name": "Administrator",
                        "is_active": True,
                        "is_superuser": True,
                        "roles": ["admin"]
                    }
                }
            ]
        }
    }


# ===========================================
# 註冊相關 Schemas
# ===========================================

class RegisterRequest(BaseModel):
    """註冊請求"""
    username: str = Field(..., description="使用者名稱", min_length=3, max_length=50)
    email: EmailStr = Field(..., description="電子郵件")
    password: str = Field(..., description="密碼", min_length=6, max_length=100)
    full_name: Optional[str] = Field(None, description="真實姓名", max_length=100)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "newuser",
                    "email": "newuser@example.com",
                    "password": "secure_password123",
                    "full_name": "New User"
                }
            ]
        }
    }


class RegisterResponse(BaseModel):
    """註冊響應"""
    id: int = Field(..., description="使用者ID")
    username: str = Field(..., description="使用者名稱")
    email: str = Field(..., description="電子郵件")
    full_name: Optional[str] = Field(None, description="真實姓名")
    is_active: bool = Field(..., description="帳號是否啟用")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "username": "newuser",
                    "email": "newuser@example.com",
                    "full_name": "New User",
                    "is_active": True
                }
            ]
        }
    }


# ===========================================
# Token 刷新相關 Schemas
# ===========================================

class RefreshTokenRequest(BaseModel):
    """刷新 Token 請求"""
    refresh_token: str = Field(..., description="刷新令牌")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                }
            ]
        }
    }


# ===========================================
# 使用者資訊相關 Schemas
# ===========================================

class UserInfo(BaseModel):
    """使用者資訊"""
    id: int = Field(..., description="使用者ID")
    username: str = Field(..., description="使用者名稱")
    email: str = Field(..., description="電子郵件")
    full_name: Optional[str] = Field(None, description="真實姓名")
    avatar_url: Optional[str] = Field(None, description="頭像URL")
    is_active: bool = Field(..., description="帳號是否啟用")
    is_superuser: bool = Field(..., description="是否為超級管理員")
    roles: List[str] = Field(default_factory=list, description="角色列表")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "username": "admin",
                    "email": "admin@example.com",
                    "full_name": "Administrator",
                    "avatar_url": "https://example.com/avatar.jpg",
                    "is_active": True,
                    "is_superuser": True,
                    "roles": ["admin", "user"]
                }
            ]
        }
    }


# ===========================================
# 通用響應 Schemas
# ===========================================

class MessageResponse(BaseModel):
    """簡單訊息響應"""
    message: str = Field(..., description="響應訊息")


# ===========================================
# 密碼變更相關 Schemas
# ===========================================

class ChangePasswordRequest(BaseModel):
    """修改密碼請求"""
    old_password: str = Field(..., description="舊密碼", min_length=6, max_length=100)
    new_password: str = Field(..., description="新密碼", min_length=6, max_length=100)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "old_password": "old_password123",
                    "new_password": "new_password456"
                }
            ]
        }
    }
