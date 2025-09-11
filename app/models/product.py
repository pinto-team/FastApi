from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum


# =====================================================
# Helpers & common value objects
# =====================================================

def _empty_to_none(v):
    if v is None:
        return None
    if isinstance(v, str) and v.strip() == "":
        return None
    return v

class PricingTier(BaseModel):
    min_qty: int
    unit_price: float
    currency: Optional[str] = None

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
    barcode: str  # GTIN/UPC/EAN
    barcode_type: Optional[str] = None

class TaxClass(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    code: str  # e.g., "grocery_basic", "alcohol"
    name: str
    description: Optional[str] = None
    default_rate: Optional[float] = None  # fallback if jurisdiction-specific rates are not resolved

# =====================================================
# PRODUCT (canonical, store/warehouse-agnostic)
# =====================================================

class ProductBase(BaseModel):
    sku: str  # canonical/base SKU (variants may have their own)
    name: str
    full_name: Optional[str] = None
    description: Optional[str] = None

    brand_id: Optional[UUID] = None
    category_id: Optional[UUID] = None

    # Identification
    barcode: Optional[str] = None  # base-level GTIN/UPC/EAN
    barcode_type: Optional[str] = None
    packaging_barcodes: Optional[List[PackagingBarcode]] = None

    # Packaging / UOM
    unit_of_sale: Optional[str] = None  # e.g., "each", "pack"
    pack_size: Optional[int] = None
    case_size: Optional[int] = None
    pallet_size: Optional[int] = None

    # Physical attributes
    attributes: Optional[Dict[str, str]] = None
    weight: Optional[float] = None
    weight_unit: Optional[str] = "kg"
    dimensions: Optional[Dimensions] = None

    # Handling & shelf life
    packaging: Optional[str] = None
    storage: Optional[str] = None  # e.g., chilled, frozen
    shelf_life_days: Optional[int] = None

    # Food specifics
    ingredients: Optional[List[str]] = None
    nutrition_facts: Optional[NutritionFacts] = None
    dietary: Optional[DietaryInfo] = None
    allergens: Optional[List[str]] = None  # e.g., ["milk", "peanuts"]

    # Catalog flags
    is_active: bool = True
    tags: Optional[List[str]] = None

    # Media
    primary_image_id: Optional[UUID] = None
    images: Optional[List[UUID]] = None  # File ids

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

    attributes: Optional[Dict[str, str]] = None
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
    brand: Optional[Brand] = None
    category: Optional[Category] = None
    images: Optional[List[File]] = None

# =====================================================
# PRODUCT VARIANTS (e.g., size/flavor/color)
# =====================================================

class ProductVariantBase(BaseModel):
    product_id: UUID
    sku: str
    name: Optional[str] = None  # display name for variant
    attributes: Optional[Dict[str, str]] = None  # e.g., {"size": "1L", "flavor": "Chocolate"}

    barcode: Optional[str] = None
    barcode_type: Optional[str] = None
    packaging_barcodes: Optional[List[PackagingBarcode]] = None

    # Optional overrides for physical details
    weight: Optional[float] = None
    weight_unit: Optional[str] = None
    dimensions: Optional[Dimensions] = None

    primary_image_id: Optional[UUID] = None
    images: Optional[List[UUID]] = None

class ProductVariantCreate(ProductVariantBase):
    pass

class ProductVariantUpdate(BaseModel):
    product_id: Optional[UUID] = None
    sku: Optional[str] = None
    name: Optional[str] = None
    attributes: Optional[Dict[str, str]] = None

    barcode: Optional[str] = None
    barcode_type: Optional[str] = None
    packaging_barcodes: Optional[List[PackagingBarcode]] = None

    weight: Optional[float] = None
    weight_unit: Optional[str] = None
    dimensions: Optional[Dimensions] = None

    primary_image_id: Optional[UUID] = None
    images: Optional[List[UUID]] = None

class ProductVariant(ProductVariantBase):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

class ProductVariantResponse(ProductVariant):
    product: Optional[Product] = None
    images: Optional[List[File]] = None

# =====================================================
# LOCALIZATION (i18n)
# =====================================================

class ProductTranslation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    product_id: UUID
    locale: str  # e.g., "fa-IR", "en-US"
    name: Optional[str] = None
    full_name: Optional[str] = None
    description: Optional[str] = None

# =====================================================
# OFFER / LISTING (per-store settings)
# =====================================================
# In a marketplace, price/policy vary by seller (store). Offers may be at product or variant level.

class OfferBase(BaseModel):
    store_id: UUID
    product_id: Optional[UUID] = None
    variant_id: Optional[UUID] = None  # if pricing differs per variant

    # Pricing
    price: float
    currency: str = "USD"
    sale_price: Optional[float] = None
    price_effective_start: Optional[datetime] = None
    price_effective_end: Optional[datetime] = None

    # Tax
    tax_class_id: Optional[UUID] = None
    tax_rate: Optional[float] = None  # override when needed

    # Tiers
    pricing_tiers: Optional[List[PricingTier]] = None

    # Availability & policy (store-level)
    allow_backorder: bool = False
    is_active: bool = True
    warranty_months: Optional[int] = None
    returnable: Optional[bool] = None

class OfferCreate(OfferBase):
    pass

class OfferUpdate(BaseModel):
    store_id: Optional[UUID] = None
    product_id: Optional[UUID] = None
    variant_id: Optional[UUID] = None

    price: Optional[float] = None
    currency: Optional[str] = None
    sale_price: Optional[float] = None
    price_effective_start: Optional[datetime] = None
    price_effective_end: Optional[datetime] = None

    tax_class_id: Optional[UUID] = None
    tax_rate: Optional[float] = None

    pricing_tiers: Optional[List[PricingTier]] = None

    allow_backorder: Optional[bool] = None
    is_active: Optional[bool] = None
    warranty_months: Optional[int] = None
    returnable: Optional[bool] = None

class Offer(OfferBase):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

class OfferResponse(Offer):
    store: Optional[Store] = None
    tax_class: Optional[TaxClass] = None

# =====================================================
# INVENTORY (per warehouse, optionally scoped to a store and/or variant)
# =====================================================

class InventoryBase(BaseModel):
    product_id: Optional[UUID] = None
    variant_id: Optional[UUID] = None
    warehouse_id: UUID
    store_id: Optional[UUID] = None  # for marketplace where warehouses belong to a store

    quantity_on_hand: int = 0
    quantity_reserved: int = 0
    incoming_qty: int = 0

    reorder_point: Optional[int] = None
    reorder_qty: Optional[int] = None

class InventoryCreate(InventoryBase):
    pass

class InventoryUpdate(BaseModel):
    product_id: Optional[UUID] = None
    variant_id: Optional[UUID] = None
    warehouse_id: Optional[UUID] = None
    store_id: Optional[UUID] = None

    quantity_on_hand: Optional[int] = None
    quantity_reserved: Optional[int] = None
    incoming_qty: Optional[int] = None

    reorder_point: Optional[int] = None
    reorder_qty: Optional[int] = None

class Inventory(InventoryBase):
    id: UUID = Field(default_factory=uuid4)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

class InventoryResponse(Inventory):
    warehouse: Optional[Warehouse] = None
    store: Optional[Store] = None

# =====================================================
# LOT-LEVEL INVENTORY (expiry/batch tracking for FEFO)
# =====================================================

class InventoryLotBase(BaseModel):
    product_id: Optional[UUID] = None
    variant_id: Optional[UUID] = None
    warehouse_id: UUID
    store_id: Optional[UUID] = None

    lot_code: str
    expiry_date: Optional[date] = None

    quantity_on_hand: int = 0
    quantity_reserved: int = 0

    cost_price: Optional[float] = None  # useful for COGS per lot

class InventoryLotCreate(InventoryLotBase):
    pass

class InventoryLotUpdate(BaseModel):
    product_id: Optional[UUID] = None
    variant_id: Optional[UUID] = None
    warehouse_id: Optional[UUID] = None
    store_id: Optional[UUID] = None

    lot_code: Optional[str] = None
    expiry_date: Optional[date] = None

    quantity_on_hand: Optional[int] = None
    quantity_reserved: Optional[int] = None

    cost_price: Optional[float] = None

class InventoryLot(InventoryLotBase):
    id: UUID = Field(default_factory=uuid4)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class InventoryLotResponse(InventoryLot):
    warehouse: Optional[Warehouse] = None
    store: Optional[Store] = None

# =====================================================
# NOTES
# - Product is store/warehouse-agnostic and holds only canonical catalog data.
# - Offer contains store-specific pricing/policies and can be at product or variant level.
# - Inventory tracks stock at warehouse level; supports variant and optional store scoping.
# - InventoryLot enables FEFO (first-expire-first-out) and recall tracking.
# - Added ProductVariant for size/flavor variants with separate SKUs & barcodes.
# - Added DietaryInfo/allergens and PackagingBarcode levels for grocery needs.
# - Added TaxClass model; Offer may reference a tax class or override with tax_rate.
# - Added ProductTranslation for i18n of name/description.
# - Added soft-delete (deleted_at) for core entities to simplify restores/audits.
# =====================================================
from pydantic import BaseModel, Field, field_validator
from uuid import UUID, uuid4
from datetime import datetime, date
from typing import Dict, List, Optional
from enum import Enum

# External models (kept as-is)
from app.models.file import File
from .brand import Brand
from .category import Category
from .store import Store
from .warehouse import Warehouse

# =====================================================
# Helpers & common value objects
# =====================================================

def _empty_to_none(v):
    if v is None:
        return None
    if isinstance(v, str) and v.strip() == "":
        return None
    return v

class PricingTier(BaseModel):
    min_qty: int
    unit_price: float
    currency: Optional[str] = None

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
    barcode: str  # GTIN/UPC/EAN
    barcode_type: Optional[str] = None

class TaxClass(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    code: str  # e.g., "grocery_basic", "alcohol"
    name: str
    description: Optional[str] = None
    default_rate: Optional[float] = None  # fallback if jurisdiction-specific rates are not resolved

# =====================================================
# PRODUCT (canonical, store/warehouse-agnostic)
# =====================================================

class ProductBase(BaseModel):
    sku: str  # canonical/base SKU (variants may have their own)
    name: str
    full_name: Optional[str] = None
    description: Optional[str] = None

    brand_id: Optional[UUID] = None
    category_id: Optional[UUID] = None

    # Identification
    barcode: Optional[str] = None  # base-level GTIN/UPC/EAN
    barcode_type: Optional[str] = None
    packaging_barcodes: Optional[List[PackagingBarcode]] = None

    # Packaging / UOM
    unit_of_sale: Optional[str] = None  # e.g., "each", "pack"
    pack_size: Optional[int] = None
    case_size: Optional[int] = None
    pallet_size: Optional[int] = None

    # Physical attributes
    attributes: Optional[Dict[str, str]] = None
    weight: Optional[float] = None
    weight_unit: Optional[str] = "kg"
    dimensions: Optional[Dimensions] = None

    # Handling & shelf life
    packaging: Optional[str] = None
    storage: Optional[str] = None  # e.g., chilled, frozen
    shelf_life_days: Optional[int] = None

    # Food specifics
    ingredients: Optional[List[str]] = None
    nutrition_facts: Optional[NutritionFacts] = None
    dietary: Optional[DietaryInfo] = None
    allergens: Optional[List[str]] = None  # e.g., ["milk", "peanuts"]

    # Catalog flags
    is_active: bool = True
    tags: Optional[List[str]] = None

    # Media
    primary_image_id: Optional[UUID] = None
    images: Optional[List[UUID]] = None  # File ids

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

    attributes: Optional[Dict[str, str]] = None
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
    brand: Optional[Brand] = None
    category: Optional[Category] = None
    images: Optional[List[File]] = None

# =====================================================
# PRODUCT VARIANTS (e.g., size/flavor/color)
# =====================================================

class ProductVariantBase(BaseModel):
    product_id: UUID
    sku: str
    name: Optional[str] = None  # display name for variant
    attributes: Optional[Dict[str, str]] = None  # e.g., {"size": "1L", "flavor": "Chocolate"}

    barcode: Optional[str] = None
    barcode_type: Optional[str] = None
    packaging_barcodes: Optional[List[PackagingBarcode]] = None

    # Optional overrides for physical details
    weight: Optional[float] = None
    weight_unit: Optional[str] = None
    dimensions: Optional[Dimensions] = None

    primary_image_id: Optional[UUID] = None
    images: Optional[List[UUID]] = None

class ProductVariantCreate(ProductVariantBase):
    pass

class ProductVariantUpdate(BaseModel):
    product_id: Optional[UUID] = None
    sku: Optional[str] = None
    name: Optional[str] = None
    attributes: Optional[Dict[str, str]] = None

    barcode: Optional[str] = None
    barcode_type: Optional[str] = None
    packaging_barcodes: Optional[List[PackagingBarcode]] = None

    weight: Optional[float] = None
    weight_unit: Optional[str] = None
    dimensions: Optional[Dimensions] = None

    primary_image_id: Optional[UUID] = None
    images: Optional[List[UUID]] = None

class ProductVariant(ProductVariantBase):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

class ProductVariantResponse(ProductVariant):
    product: Optional[Product] = None
    images: Optional[List[File]] = None

# =====================================================
# LOCALIZATION (i18n)
# =====================================================

class ProductTranslation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    product_id: UUID
    locale: str  # e.g., "fa-IR", "en-US"
    name: Optional[str] = None
    full_name: Optional[str] = None
    description: Optional[str] = None

# =====================================================
# OFFER / LISTING (per-store settings)
# =====================================================
# In a marketplace, price/policy vary by seller (store). Offers may be at product or variant level.

class OfferBase(BaseModel):
    store_id: UUID
    product_id: Optional[UUID] = None
    variant_id: Optional[UUID] = None  # if pricing differs per variant

    # Pricing
    price: float
    currency: str = "USD"
    sale_price: Optional[float] = None
    price_effective_start: Optional[datetime] = None
    price_effective_end: Optional[datetime] = None

    # Tax
    tax_class_id: Optional[UUID] = None
    tax_rate: Optional[float] = None  # override when needed

    # Tiers
    pricing_tiers: Optional[List[PricingTier]] = None

    # Availability & policy (store-level)
    allow_backorder: bool = False
    is_active: bool = True
    warranty_months: Optional[int] = None
    returnable: Optional[bool] = None

class OfferCreate(OfferBase):
    pass

class OfferUpdate(BaseModel):
    store_id: Optional[UUID] = None
    product_id: Optional[UUID] = None
    variant_id: Optional[UUID] = None

    price: Optional[float] = None
    currency: Optional[str] = None
    sale_price: Optional[float] = None
    price_effective_start: Optional[datetime] = None
    price_effective_end: Optional[datetime] = None

    tax_class_id: Optional[UUID] = None
    tax_rate: Optional[float] = None

    pricing_tiers: Optional[List[PricingTier]] = None

    allow_backorder: Optional[bool] = None
    is_active: Optional[bool] = None
    warranty_months: Optional[int] = None
    returnable: Optional[bool] = None

class Offer(OfferBase):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

class OfferResponse(Offer):
    store: Optional[Store] = None
    tax_class: Optional[TaxClass] = None

# =====================================================
# INVENTORY (per warehouse, optionally scoped to a store and/or variant)
# =====================================================

class InventoryBase(BaseModel):
    product_id: Optional[UUID] = None
    variant_id: Optional[UUID] = None
    warehouse_id: UUID
    store_id: Optional[UUID] = None  # for marketplace where warehouses belong to a store

    quantity_on_hand: int = 0
    quantity_reserved: int = 0
    incoming_qty: int = 0

    reorder_point: Optional[int] = None
    reorder_qty: Optional[int] = None

class InventoryCreate(InventoryBase):
    pass

class InventoryUpdate(BaseModel):
    product_id: Optional[UUID] = None
    variant_id: Optional[UUID] = None
    warehouse_id: Optional[UUID] = None
    store_id: Optional[UUID] = None

    quantity_on_hand: Optional[int] = None
    quantity_reserved: Optional[int] = None
    incoming_qty: Optional[int] = None

    reorder_point: Optional[int] = None
    reorder_qty: Optional[int] = None

class Inventory(InventoryBase):
    id: UUID = Field(default_factory=uuid4)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

class InventoryResponse(Inventory):
    warehouse: Optional[Warehouse] = None
    store: Optional[Store] = None

# =====================================================
# LOT-LEVEL INVENTORY (expiry/batch tracking for FEFO)
# =====================================================

class InventoryLotBase(BaseModel):
    product_id: Optional[UUID] = None
    variant_id: Optional[UUID] = None
    warehouse_id: UUID
    store_id: Optional[UUID] = None

    lot_code: str
    expiry_date: Optional[date] = None

    quantity_on_hand: int = 0
    quantity_reserved: int = 0

    cost_price: Optional[float] = None  # useful for COGS per lot

class InventoryLotCreate(InventoryLotBase):
    pass

class InventoryLotUpdate(BaseModel):
    product_id: Optional[UUID] = None
    variant_id: Optional[UUID] = None
    warehouse_id: Optional[UUID] = None
    store_id: Optional[UUID] = None

    lot_code: Optional[str] = None
    expiry_date: Optional[date] = None

    quantity_on_hand: Optional[int] = None
    quantity_reserved: Optional[int] = None

    cost_price: Optional[float] = None

class InventoryLot(InventoryLotBase):
    id: UUID = Field(default_factory=uuid4)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class InventoryLotResponse(InventoryLot):
    warehouse: Optional[Warehouse] = None
    store: Optional[Store] = None

# =====================================================
# NOTES
# - Product is store/warehouse-agnostic and holds only canonical catalog data.
# - Offer contains store-specific pricing/policies and can be at product or variant level.
# - Inventory tracks stock at warehouse level; supports variant and optional store scoping.
# - InventoryLot enables FEFO (first-expire-first-out) and recall tracking.
# - Added ProductVariant for size/flavor variants with separate SKUs & barcodes.
# - Added DietaryInfo/allergens and PackagingBarcode levels for grocery needs.
# - Added TaxClass model; Offer may reference a tax class or override with tax_rate.
# - Added ProductTranslation for i18n of name/description.
# - Added soft-delete (deleted_at) for core entities to simplify restores/audits.
# =====================================================
