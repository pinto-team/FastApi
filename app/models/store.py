from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime
from typing import List

class StoreBase(BaseModel):
    name: str
    description: str | None = None
    address: str | None = None
    phone: str | None = None
    owner_id: UUID | None = None
    warehouse_ids: List[UUID] | None = None

class StoreCreate(StoreBase):
    pass

class StoreUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    address: str | None = None
    phone: str | None = None
    owner_id: UUID | None = None
    warehouse_ids: List[UUID] | None = None

class Store(StoreBase):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
