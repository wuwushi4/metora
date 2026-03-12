# -*- coding: utf-8 -*-
"""
使用者管理相關的 Pydantic Schemas
定義使用者 CRUD 的 API 請求和響應結構
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator


# ===========================================
# 使用者 CRUD Schemas
# ===========================================

class UserCreate(BaseModel):
    """建立使用者請求"""
    username: str = Field(..., description="使用者名稱", min_length=3, max_length=50)
    email: EmailStr = Field(..., description="電子郵件")
    password: str = Field(..., description="密碼", min_length=6, max_length=100)
    full_name: Optional[str] = Field(None, description="真實姓名", max_length=100)
    roles: Optional[List[str]] = Field(default=["user"], description="角色列表")

    @field_validator('username', 'password')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """清除前後空白字符"""
        return v.strip() if v else v

    @field_validator('full_name')
    @classmethod
    def strip_full_name(cls, v: Optional[str]) -> Optional[str]:
        """清除真實姓名的前後空白字符"""
        return v.strip() if v else v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "newuser",
                    "email": "newuser@example.com",
                    "password": "secure_password123",
                    "full_name": "New User",
                    "roles": ["user"]
                }
            ]
        }
    }


class UserUpdate(BaseModel):
    """更新使用者請求（部分更新）"""
    email: Optional[EmailStr] = Field(None, description="電子郵件")
    full_name: Optional[str] = Field(None, description="真實姓名", max_length=100)
    is_active: Optional[bool] = Field(None, description="帳號是否啟用")

    @field_validator('full_name')
    @classmethod
    def strip_full_name(cls, v: Optional[str]) -> Optional[str]:
        """清除真實姓名的前後空白字符"""
        return v.strip() if v else v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "updated@example.com",
                    "full_name": "Updated Name",
                    "is_active": True
                }
            ]
        }
    }


class UserResponse(BaseModel):
    """使用者響應"""
    id: int = Field(..., description="使用者ID")
    username: str = Field(..., description="使用者名稱")
    email: str = Field(..., description="電子郵件")
    full_name: Optional[str] = Field(None, description="真實姓名")
    is_active: bool = Field(..., description="帳號是否啟用")
    is_superuser: bool = Field(..., description="是否為超級管理員")
    created_at: datetime = Field(..., description="建立時間")
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
                    "is_active": True,
                    "is_superuser": True,
                    "created_at": "2024-01-01T00:00:00Z",
                    "roles": ["admin", "user"]
                }
            ]
        }
    }


class UserListParams(BaseModel):
    """使用者列表查詢參數"""
    page: int = Field(default=1, ge=1, description="頁碼（從 1 開始）")
    page_size: int = Field(default=20, ge=1, le=100, description="每頁筆數（1-100）")
    username: Optional[str] = Field(None, description="使用者名稱（模糊搜尋）")
    email: Optional[str] = Field(None, description="電子郵件（模糊搜尋）")
    is_active: Optional[bool] = Field(None, description="是否啟用（精確搜尋）")
    role: Optional[str] = Field(None, description="角色（精確搜尋）")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "page": 1,
                    "page_size": 20,
                    "username": "admin",
                    "is_active": True,
                    "role": "admin"
                }
            ]
        }
    }


class AssignRolesRequest(BaseModel):
    """分配角色請求"""
    roles: List[str] = Field(..., description="角色名稱列表", min_length=1)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "roles": ["admin", "user"]
                }
            ]
        }
    }
