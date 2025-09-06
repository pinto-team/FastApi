# app/services/warehouse_service.py
from uuid import UUID, uuid4
from datetime import datetime
from typing import Tuple, List

from fastapi import HTTPException

from app.db.mongo import db
from app.models.warehouse import Warehouse, WarehouseCreate, WarehouseUpdate

class WarehouseService:
    def __init__(self):
        self.collection = db["warehouses"]

    async def create(self, data: WarehouseCreate) -> Warehouse:
        now = datetime.utcnow()
        payload = data.dict(exclude_unset=True)

        # اگر نیاز داری manager_id بررسی وجودی شود، اینجا انجام بده
        # if payload.get("manager_id"):
        #     manager = await users_service.get(payload["manager_id"])
        #     if not manager:
        #         raise HTTPException(status_code=400, detail="Manager not found")

        payload.setdefault("id", uuid4())
        payload.setdefault("created_at", now)
        payload.setdefault("updated_at", now)

        await self.collection.insert_one(payload)
        return Warehouse(**payload)

    async def get(self, id_: UUID) -> Warehouse | None:
        doc = await self.collection.find_one({"id": id_})
        return Warehouse(**doc) if doc else None

    async def update(self, id_: UUID, data: WarehouseUpdate) -> Warehouse | None:
        patch = data.dict(exclude_unset=True)

        # اگر نیاز داری manager_id بررسی شود
        # if "manager_id" in patch and patch["manager_id"]:
        #     manager = await users_service.get(patch["manager_id"])
        #     if not manager:
        #         raise HTTPException(status_code=400, detail="Manager not found")

        patch["updated_at"] = datetime.utcnow()

        res = await self.collection.update_one({"id": id_}, {"$set": patch})
        if res.matched_count == 0:
            return None

        doc = await self.collection.find_one({"id": id_})
        return Warehouse(**doc) if doc else None

    async def delete(self, id_: UUID) -> bool:
        res = await self.collection.delete_one({"id": id_})
        return res.deleted_count > 0

    async def list(self, filters: dict | None, page: int, limit: int) -> Tuple[List[Warehouse], int]:
        q = {k: v for k, v in (filters or {}).items() if v is not None}
        cursor = (
            self.collection
            .find(q)
            .skip((page - 1) * limit)
            .limit(limit)
            .sort("created_at", -1)
        )
        items = [Warehouse(**doc) async for doc in cursor]
        total = await self.collection.count_documents(q)
        return items, total

warehouse_service = WarehouseService()
