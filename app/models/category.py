# app/models/category.py
from pydantic import BaseModel, Field, field_validator  # <-- field_validator اضافه
from typing import Optional, List
from datetime import datetime

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    order: Optional[int] = None
    # برای نمایش در خروجی
    image_url: Optional[str] = None  # NEW

class CategoryCreate(CategoryBase):
    # ورودی کلاینت
    image_id: Optional[str] = None   # NEW

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
    parent_id: Optional[str] = None
    order: Optional[int] = None
    image_id: Optional[str] = None   # NEW
    # اجازه بده سرور image_url را هم ست/پاک کند (مثل برند)
    image_url: Optional[str] = None  # NEW

    @field_validator("image_id", mode="before")
    @classmethod
    def _image_id_empty_string_to_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

class Category(CategoryBase):
    id: str
    created_at: datetime
    updated_at: datetime
    image_id: Optional[str] = None  # NEW

class ReorderCategory(BaseModel):
    id: str
    order: int
