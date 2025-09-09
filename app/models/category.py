from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    order: Optional[int] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    order: Optional[int] = None

class Category(CategoryBase):
    id: str
    created_at: datetime
    updated_at: datetime

class ReorderCategory(BaseModel):
    id: str
    order: int