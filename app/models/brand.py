from pydantic import BaseModel, Field, field_validator
from uuid import UUID, uuid4
from datetime import datetime

class BrandBase(BaseModel):
    name: str
    description: str | None = None
    country: str | None = None
    website: str | None = None
    # فقط برای خروجی/نمایش
    logo_url: str | None = None

class BrandCreate(BaseModel):
    name: str
    description: str | None = None
    country: str | None = None
    website: str | None = None
    # ورودی از کلاینت:
    logo_id: UUID | None = None
    # سرور پس از ترجمه‌ی id پر می‌کند (کلاینت نفرستد!)
    logo_url: str | None = None

    # فیکس 422: رشته‌ی خالی را None کن
    @field_validator("logo_id", mode="before")
    @classmethod
    def _logo_id_empty_string_to_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

class BrandUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    country: str | None = None
    website: str | None = None
    logo_id: UUID | None = None
    # اجازه بده سرور در آپدیت هم logo_url را ست/پاک کند
    logo_url: str | None = None

    # فیکس 422: رشته‌ی خالی را None کن (پشتیبانی از پاک‌کردن لوگو با "")
    @field_validator("logo_id", mode="before")
    @classmethod
    def _logo_id_empty_string_to_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

class Brand(BrandBase):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    logo_id: UUID | None = None

class Pagination(BaseModel):
    page: int
    limit: int
    total: int

class BrandListResponse(BaseModel):
    items: list[Brand]
    pagination: Pagination
