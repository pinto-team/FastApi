from pydantic import BaseModel, Field, field_validator
from uuid import UUID, uuid4
from datetime import datetime

class WarehouseBase(BaseModel):
    name: str
    location: str | None = None
    capacity: int | None = None
    manager_id: UUID | None = None

class WarehouseCreate(BaseModel):
    name: str
    location: str | None = None
    capacity: int | None = None
    manager_id: UUID | None = None

    # فیکس 422: رشته‌ی خالی → None
    @field_validator("manager_id", mode="before")
    @classmethod
    def _manager_id_empty_string_to_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

class WarehouseUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    capacity: int | None = None
    manager_id: UUID | None = None

    # فیکس 422: رشته‌ی خالی → None
    @field_validator("manager_id", mode="before")
    @classmethod
    def _manager_id_empty_string_to_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

class Warehouse(WarehouseBase):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class WarehouseStock(BaseModel):
    warehouse_id: UUID
    product_id: UUID
    quantity: int
    batch_number: str | None = None
    expiry_date: datetime | None = None
