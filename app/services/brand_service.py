# app/services/brand_service.py
from uuid import UUID, uuid4
from datetime import datetime
from typing import Tuple, List

from fastapi import HTTPException

from app.db.mongo import db
from app.models.brand import Brand, BrandCreate, BrandUpdate


class BrandService:
    def __init__(self):
        self.collection = db["brands"]

    async def create(self, data: BrandCreate) -> Brand:
        now = datetime.utcnow()
        data_dict = data.dict(exclude_unset=True)

        # اگر logo_id هست ولی logo_url نیومده
        if data_dict.get("logo_id") and not data_dict.get("logo_url"):
            raise HTTPException(status_code=400, detail="logo_url must be set by server for given logo_id")

        new_id = uuid4()
        data_dict["_id"] = str(new_id)  # برای Mongo (string)
        data_dict["id"] = new_id  # برای اپلیکیشن (UUID)
        data_dict.setdefault("created_at", now)
        data_dict.setdefault("updated_at", now)

        await self.collection.insert_one(data_dict)
        return Brand(**data_dict)

    async def get(self, id_: UUID) -> Brand | None:
        doc = await self.collection.find_one({"id": id_})
        return Brand(**doc) if doc else None

    async def update(self, id_: UUID, data: BrandUpdate) -> Brand | None:
        patch = data.dict(exclude_unset=True)
        # اگر logo_id کلیدش در پچ هست ولی مقدارش truthy است، باید logo_url هم باشد.
        if "logo_id" in patch and patch.get("logo_id") and not patch.get("logo_url"):
            raise HTTPException(status_code=400, detail="logo_url must be set by server for given logo_id")

        patch["updated_at"] = datetime.utcnow()

        await self.collection.update_one({"id": id_}, {"$set": patch})
        doc = await self.collection.find_one({"id": id_})
        return Brand(**doc) if doc else None

    async def delete(self, id_: UUID) -> bool:
        res = await self.collection.delete_one({"id": id_})
        return res.deleted_count > 0

    async def list(self, filters: dict | None, page: int, limit: int) -> Tuple[List[Brand], int]:
        q = {k: v for k, v in (filters or {}).items() if v is not None}
        cursor = (
            self.collection
            .find(q)
            .skip((page - 1) * limit)
            .limit(limit)
            .sort("created_at", -1)
        )
        items = [Brand(**doc) async for doc in cursor]
        total = await self.collection.count_documents(q)
        return items, total


brand_service = BrandService()
