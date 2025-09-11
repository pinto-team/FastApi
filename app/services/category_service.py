# app/services/category_service.py
from typing import List, Tuple, Optional
from uuid import uuid4, UUID
from datetime import datetime
import logging

from .base import MongoCRUD
from app.models.category import Category, CategoryCreate, CategoryUpdate, ReorderCategory
from ..db.mongo import db

logger = logging.getLogger("app.services.category_service")


class CategoryService(MongoCRUD):
    """
    Service layer for Category CRUD + ordering logic.
    Backed by a Mongo collection with the following key indexes:
      - uniq_id:        unique(id)
      - idx_parent_ord: (parent_id, order)
      - uniq_name_pp:   unique(parent_id, name)
    """

    def __init__(self):
        super().__init__(
            collection="categories",
            model_cls=Category,
            create_cls=CategoryCreate,
            update_cls=CategoryUpdate,
        )

    # ----------------------
    # Indexes
    # ----------------------
    async def ensure_indexes(self) -> None:
        await self.collection.create_index([("id", 1)], name="uniq_id", unique=True)
        await self.collection.create_index([("parent_id", 1), ("order", 1)], name="idx_parent_order")
        await self.collection.create_index(
            [("parent_id", 1), ("name", 1)],
            name="uniq_name_per_parent",
            unique=True,
        )
        logger.info("✅ Category indexes ensured.")

    # ----------------------
    # File helpers
    # ----------------------
    async def _find_file_by_any_id(self, img_id_str: str) -> Optional[dict]:
        """
        جستجو فایل با id به صورت str یا UUID
        """
        or_clauses = [{"id": img_id_str}, {"_id": img_id_str}]
        try:
            img_uuid = UUID(img_id_str)
            or_clauses.append({"id": img_uuid})
        except Exception:
            pass
        return await db["files"].find_one({"$or": or_clauses}, projection={"url": 1, "id": 1})

    async def _autofill_image_url(self, data: dict) -> None:
        """
        اگر image_id موجود باشد ولی image_url نیاید → پر کردن خودکار
        اگر image_id None یا رشته‌ی خالی باشد → پاک کردن هر دو
        """
        if "image_id" in data:
            img_id = data.get("image_id")
            if img_id is None or (isinstance(img_id, str) and img_id.strip() == ""):
                data["image_id"] = None
                data["image_url"] = None
                return
            if img_id and not data.get("image_url"):
                file_doc = await self._find_file_by_any_id(str(img_id))
                if not file_doc:
                    raise ValueError("invalid image_id")
                data["image_url"] = file_doc.get("url")

    # ----------------------
    # Helpers
    # ----------------------
    async def _next_order(self, parent_id: Optional[UUID]) -> int:
        query = {"parent_id": parent_id}
        doc = await (
            self.collection.find(query)
            .sort("order", -1)
            .limit(1)
            .to_list(1)
        )
        return (doc[0].get("order", -1) + 1) if doc else 0

    async def _validate_no_loop(self, id_: UUID, parent_id: Optional[UUID]) -> None:
        current_id = parent_id
        while current_id:
            if current_id == id_:
                raise ValueError("Cannot set a child category as parent (loop detected)")
            parent = await self.get(current_id)
            if not parent:
                break
            current_id = parent.parent_id

    async def _check_name_uniqueness(
        self, name: str, parent_id: Optional[UUID], exclude_id: Optional[UUID] = None
    ) -> None:
        query: dict = {"name": name, "parent_id": parent_id}
        if exclude_id:
            query["id"] = {"$ne": exclude_id}
        exists = await self.collection.find_one(query, projection={"_id": 1})
        if exists:
            raise ValueError(f"Category with name '{name}' already exists under the same parent")

    # ----------------------
    # CRUD
    # ----------------------
    async def create(self, payload: CategoryCreate) -> Category:
        if payload.parent_id:
            parent = await self.get(payload.parent_id)
            if not parent:
                raise ValueError(f"Parent category with id {payload.parent_id} does not exist")

        await self._check_name_uniqueness(payload.name, payload.parent_id)

        data = payload.model_dump(exclude_unset=True)

        # 👇 هم _id و هم id ست می‌کنیم
        new_id = uuid4()
        data["_id"] = str(new_id)  # برای Mongo
        data["id"] = new_id  # برای اپلیکیشن

        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()

        if data.get("order") is None:
            data["order"] = await self._next_order(payload.parent_id)

        await self._autofill_image_url(data)
        await self.collection.insert_one(data)
        return Category(**data)

    async def get(self, id_: UUID) -> Optional[Category]:
        doc = await self.collection.find_one({"id": id_})
        return Category(**doc) if doc else None

    async def list(self, filters: Optional[dict], page: int, limit: int) -> Tuple[List[Category], int]:
        query = filters or {}
        cursor = (
            self.collection.find(query)
            .skip((page - 1) * limit)
            .limit(limit)
            .sort([("parent_id", 1), ("order", 1)])
        )
        items = [Category(**doc) async for doc in cursor]
        total = await self.collection.count_documents(query)
        return items, total

    async def update(self, id_: UUID, payload: CategoryUpdate) -> Optional[Category]:
        current = await self.collection.find_one({"id": id_})
        if not current:
            return None

        if "parent_id" in payload.model_fields_set:
            new_parent_id = payload.parent_id
            if new_parent_id:
                await self._validate_no_loop(id_, new_parent_id)
                parent = await self.get(new_parent_id)
                if not parent:
                    raise ValueError(f"Parent category with id {new_parent_id} does not exist")

        new_name = payload.name if "name" in payload.model_fields_set else current.get("name")
        new_parent_id = (
            payload.parent_id if "parent_id" in payload.model_fields_set else current.get("parent_id")
        )
        await self._check_name_uniqueness(new_name, new_parent_id, exclude_id=id_)

        update_doc = payload.model_dump(exclude_unset=True)
        await self._autofill_image_url(update_doc)
        update_doc["updated_at"] = datetime.utcnow()

        updated = await self.collection.find_one_and_update(
            {"id": id_},
            {"$set": update_doc},
            return_document=True,
        )
        return Category(**updated) if updated else None

    async def _collect_descendant_ids(self, root_id: UUID) -> List[UUID]:
        descendants: List[UUID] = []
        queue: List[UUID] = [root_id]

        while queue:
            current_batch = queue[:100]
            queue = queue[100:]

            cursor = self.collection.find(
                {"parent_id": {"$in": current_batch}},
                projection={"id": 1}
            )
            children = [doc["id"] async for doc in cursor]

            if not children:
                continue

            descendants.extend(children)
            queue.extend(children)

        return descendants

    async def delete(self, id_: UUID) -> bool:
        current = await self.collection.find_one({"id": id_}, projection={"id": 1})
        if not current:
            return False

        descendants = await self._collect_descendant_ids(id_)
        ids_to_delete = [id_] + descendants

        result = await self.collection.delete_many({"id": {"$in": ids_to_delete}})
        return result.deleted_count > 0

    # ----------------------
    # Reordering
    # ----------------------
    async def reorder(self, payload: List[ReorderCategory]) -> bool:
        if not payload:
            return True

        parent_ids = set()
        orders = set()

        for item in payload:
            if item.order is None or item.order < 0:
                raise ValueError("Order must be a non-negative integer")

            category = await self.get(item.id)
            if not category:
                raise ValueError(f"Category with id {item.id} not found")

            parent_ids.add(category.parent_id)
            if item.order in orders:
                raise ValueError(f"Duplicate order value {item.order}")
            orders.add(item.order)

        if len(parent_ids) > 1:
            raise ValueError("All categories must have the same parent_id")

        now = datetime.utcnow()
        for item in payload:
            await self.collection.update_one(
                {"id": item.id},
                {"$set": {"order": item.order, "updated_at": now}},
            )
        return True

    async def reorder_single(self, category_id: UUID, new_order: int) -> bool:
        if new_order < 0:
            raise ValueError("Order cannot be negative")

        target = await self.get(category_id)
        if not target:
            raise ValueError("Category not found")

        parent_id = target.parent_id
        current_order = target.order

        if new_order == current_order:
            return True

        direction = 1 if new_order > current_order else -1
        low, high = (current_order, new_order) if current_order <= new_order else (new_order, current_order)

        await self.collection.update_many(
            {
                "parent_id": parent_id,
                "order": {"$gte": low, "$lte": high},
                "id": {"$ne": category_id},
            },
            {
                "$inc": {"order": -direction},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )

        await self.collection.update_one(
            {"id": category_id},
            {"$set": {"order": new_order, "updated_at": datetime.utcnow()}},
        )
        return True


# Singleton
category_service = CategoryService()
