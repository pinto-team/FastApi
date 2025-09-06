from app.models.category import Category, CategoryCreate, CategoryUpdate
from .base import MongoCRUD
from typing import Tuple, List
from uuid import UUID, uuid4
from datetime import datetime

class CategoryService(MongoCRUD):
    def __init__(self):
        super().__init__(
            collection="categories",
            model_cls=Category,
            create_cls=CategoryCreate,
            update_cls=CategoryUpdate
        )

    async def create(self, payload: CategoryCreate) -> Category:
        # ✅ بررسی parent_id
        if payload.parent_id:
            parent = await self.get(payload.parent_id)
            if not parent:
                raise ValueError(f"Parent category with id {payload.parent_id} does not exist")

        data = payload.dict(exclude_unset=True)
        data.setdefault("id", str(uuid4()))   # 👈 ذخیره id به صورت string
        data.setdefault("created_at", datetime.utcnow())
        data.setdefault("updated_at", datetime.utcnow())

        await self.collection.insert_one(data)
        return Category(**data)

    async def get(self, id_: UUID) -> Category | None:
        doc = await self.collection.find_one({"id": str(id_)})  # 👈 جستجو با str
        return Category(**doc) if doc else None

    async def update(self, id_: UUID, patch: CategoryUpdate) -> Category | None:
        if patch.parent_id:
            parent = await self.get(patch.parent_id)
            if not parent:
                raise ValueError(f"Parent category with id {patch.parent_id} does not exist")

        patch_dict = patch.dict(exclude_unset=True)
        patch_dict["updated_at"] = datetime.utcnow()

        await self.collection.update_one({"id": str(id_)}, {"$set": patch_dict})  # 👈 فیلتر با str
        doc = await self.collection.find_one({"id": str(id_)})
        return Category(**doc) if doc else None

    async def delete(self, id_: UUID) -> bool:
        res = await self.collection.delete_one({"id": str(id_)})  # 👈 فیلتر با str
        return res.deleted_count > 0

    async def list(self, filters: dict | None, page: int, limit: int) -> Tuple[List[Category], int]:
        q = {k: (str(v) if isinstance(v, UUID) else v) for k, v in (filters or {}).items() if v is not None}
        cursor = (
            self.collection
            .find(q)
            .skip((page - 1) * limit)
            .limit(limit)
            .sort("created_at", -1)
        )
        items = [Category(**doc) async for doc in cursor]
        total = await self.collection.count_documents(q)
        return items, total

category_service = CategoryService()
