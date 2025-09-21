from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

# -------- فقط ورودی مجاز از کلاینت --------
class UserRegister(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: Optional[EmailStr] = None
    region: Optional[str] = None

# -------- فقط برای آپدیت (مثلا بعدا) --------
class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    region: Optional[str] = None

# -------- خروجی / ذخیره در دیتابیس --------
class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    first_name: str
    last_name: str
    phone: str
    email: Optional[EmailStr] = None
    region: Optional[str] = None

    email_verified: bool = False
    phone_verified: bool = False
    referral_code: Optional[str] = None
    inviter_user_id: Optional[str] = None
    status: str = "ACTIVE"

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
