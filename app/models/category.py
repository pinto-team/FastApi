from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[UUID] = None   # 👈 الان UUID
    order: Optional[int] = None
    image_url: Optional[str] = None  # برای نمایش در خروجی


class CategoryCreate(CategoryBase):
    # ورودی کلاینت
    image_id: Optional[str] = None

    # فیکس 422: رشته‌ی خالی را None کن
    @field_validator("image_id", mode="before")
    @classmethod
    def _image_id_empty_string_to_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[UUID] = None   # 👈 الان UUID
    order: Optional[int] = None
    image_id: Optional[str] = None
    image_url: Optional[str] = None  # اجازه بده سرور image_url را هم ست/پاک کند

    @field_validator("image_id", mode="before")
    @classmethod
    def _image_id_empty_string_to_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class Category(CategoryBase):
    id: UUID = Field(default_factory=uuid4)   # 👈 الان UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    image_id: Optional[str] = None


class ReorderCategory(BaseModel):
    id: UUID   # 👈 الان UUID
    order: int
