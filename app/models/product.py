from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from uuid import UUID, uuid4
from datetime import datetime
from typing import Dict, List, Optional, Union
from enum import Enum

# External models used in the response
from app.models.file import File
from .brand import Brand
from .category import Category

# -----------------------------
# Helpers
# -----------------------------
def _empty_to_none(v):
    if v is None:
        return None
    if isinstance(v, str) and v.strip() == "":
        return None
    return v

# برای key-value آزادِ ویژگی‌ها
AttrValue = Union[str, int, float, bool, None]

# -----------------------------
# Value Objects
# -----------------------------
class Dimensions(BaseModel):
    length: float
    width: float
    height: float
    unit: str = "cm"

class NutritionFacts(BaseModel):
    calories: Optional[float] = None
    fat: Optional[float] = None
    protein: Optional[float] = None
    carbohydrates: Optional[float] = None

class DietaryInfo(BaseModel):
    halal: Optional[bool] = None
    kosher: Optional[bool] = None
    vegetarian: Optional[bool] = None
    vegan: Optional[bool] = None
    gluten_free: Optional[bool] = None

class PackagingLevel(str, Enum):
    EACH = "each"
    PACK = "pack"
    CASE = "case"
    PALLET = "pallet"

class PackagingBarcode(BaseModel):
    level: PackagingLevel = PackagingLevel.EACH
    barcode: str               # GTIN/UPC/EAN
    barcode_type: Optional[str] = None  # مثل EAN13

# -----------------------------
# Product Models
# -----------------------------
class ProductBase(BaseModel):
    sku: str
    name: str
    full_name: Optional[str] = None
    description: Optional[str] = None

    brand_id: Optional[UUID] = None
    category_id: Optional[UUID] = None

    # Identification
    barcode: Optional[str] = None
    barcode_type: Optional[str] = None
    packaging_barcodes: Optional[List[PackagingBarcode]] = None

    # Packaging / UOM
    unit_of_sale: Optional[str] = None
    pack_size: Optional[int] = None
    case_size: Optional[int] = None
    pallet_size: Optional[int] = None

    # Physical attributes
    attributes: Optional[Dict[str, AttrValue]] = None  # key–value آزاد
    weight: Optional[float] = None
    weight_unit: Optional[str] = "kg"
    dimensions: Optional[Dimensions] = None

    # Handling & shelf life
    packaging: Optional[str] = None
    storage: Optional[str] = None
    shelf_life_days: Optional[int] = None

    # Food specifics
    ingredients: Optional[List[str]] = None
    nutrition_facts: Optional[NutritionFacts] = None
    dietary: Optional[DietaryInfo] = None
    allergens: Optional[List[str]] = None

    # Catalog flags
    is_active: bool = True
    tags: Optional[List[str]] = None

    # Media
    primary_image_id: Optional[UUID] = None
    images: Optional[List[UUID]] = None  # ورودی: لیست idها

    @field_validator("brand_id", "category_id", mode="before")
    @classmethod
    def _ids_empty_to_none(cls, v):
        return _empty_to_none(v)

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    full_name: Optional[str] = None
    description: Optional[str] = None
    brand_id: Optional[UUID] = None
    category_id: Optional[UUID] = None

    barcode: Optional[str] = None
    barcode_type: Optional[str] = None
    packaging_barcodes: Optional[List[PackagingBarcode]] = None

    unit_of_sale: Optional[str] = None
    pack_size: Optional[int] = None
    case_size: Optional[int] = None
    pallet_size: Optional[int] = None

    attributes: Optional[Dict[str, AttrValue]] = None
    weight: Optional[float] = None
    weight_unit: Optional[str] = None
    dimensions: Optional[Dimensions] = None

    packaging: Optional[str] = None
    storage: Optional[str] = None
    shelf_life_days: Optional[int] = None

    ingredients: Optional[List[str]] = None
    nutrition_facts: Optional[NutritionFacts] = None
    dietary: Optional[DietaryInfo] = None
    allergens: Optional[List[str]] = None

    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None

    primary_image_id: Optional[UUID] = None
    images: Optional[List[UUID]] = None

    @field_validator("brand_id", "category_id", mode="before")
    @classmethod
    def _ids_empty_to_none(cls, v):
        return _empty_to_none(v)

class Product(ProductBase):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

class ProductResponse(Product):
    # خروجی: تصاویر به‌صورت آبجکت فایل
    brand: Optional[Brand] = None
    category: Optional[Category] = None
    images: Optional[List[File]] = None
