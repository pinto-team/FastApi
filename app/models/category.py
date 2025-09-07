from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4
from datetime import datetime

# مدل پایه برای Category
class CategoryBase(BaseModel):
    name: str
    description: str | None = None
    parent_id: UUID | None = None
    image_url: str | None = None

    @validator("parent_id", pre=True)
    def empty_str_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v

# برای ساخت Category جدید
class CategoryCreate(CategoryBase):
    pass

# برای آپدیت Category
class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    parent_id: UUID | None = None
    image_url: str | None = None

    @validator("parent_id", pre=True)
    def empty_str_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v

# مدل اصلی Category در دیتابیس
class Category(CategoryBase):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# مدل Pagination مشترک (مثل برند)
class Pagination(BaseModel):
    page: int
    limit: int
    total: int

# مدل لیست دسته‌ها + Pagination
class CategoryListResponse(BaseModel):
    items: list[Category]
    pagination: Pagination
