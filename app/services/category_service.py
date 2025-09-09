# app/services/category_service.py
from typing import List, Tuple, Optional
from uuid import uuid4, UUID
from datetime import datetime
import logging

from .base import MongoCRUD
from app.models.category import Category, CategoryCreate, CategoryUpdate, ReorderCategory
from ..db.mongo import db  # برای خواندن فایل‌ها

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
    # Indexes (مثل قبل)
    # ----------------------
    async def ensure_indexes(self) -> None:
        """Create required indexes (id, parent/order, unique name per parent)."""
        await self.collection.create_index([("id", 1)], name="uniq_id", unique=True)
        await self.collection.create_index([("parent_id", 1), ("order", 1)], name="idx_parent_order")
        await self.collection.create_index(
            [("parent_id", 1), ("name", 1)],
            name="uniq_name_per_parent",
            unique=True,
        )
        logger.info("✅ Category indexes ensured.")

    # ----------------------
    # File helpers (جدید)
    # ----------------------
    async def _find_file_by_any_id(self, img_id_str: str) -> Optional[dict]:
        """
        فایل را هم با id (str/UUID Binary subtype 4) و هم با _id (str) جستجو می‌کند.
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
        اگر image_id باشد و image_url نیاید، url را از کالکشن files پر می‌کند.
        اگر image_id تهی/None باشد و کلیدش در ورودی باشد، هر دو فیلد پاک می‌شوند.
        """
        if "image_id" in data:
            img_id = data.get("image_id")

            # پاک کردن تصویر
            if img_id is None or (isinstance(img_id, str) and img_id.strip() == ""):
                data["image_id"] = None
                data["image_url"] = None
                return

            # پر کردن خودکار url
            if img_id and not data.get("image_url"):
                file_doc = await self._find_file_by_any_id(str(img_id))
                if not file_doc:
                    raise ValueError("invalid image_id")
                data["image_url"] = file_doc.get("url")

    # ----------------------
    # Helpers (مثل قبل)
    # ----------------------
    async def _next_order(self, parent_id: Optional[str]) -> int:

        """
        Returns the next 'order' value under the given parent.
        If none found, returns 0.
        """
        query = {"parent_id": parent_id}  # parent_id can be None (root)
        doc = await (
            self.collection.find(query)
            .sort("order", -1)
            .limit(1)
            .to_list(1)
        )
        return (doc[0].get("order", -1) + 1) if doc else 0

    async def _validate_no_loop(self, id_: str, parent_id: Optional[str]) -> None:
        """
        Ensure that setting parent_id does not introduce a cycle.
        """
        current_id = parent_id
        while current_id:
            if current_id == id_:
                raise ValueError("Cannot set a child category as parent (loop detected)")
            parent = await self.get(current_id)
            if not parent:
                break
            current_id = parent.parent_id

    async def _check_name_uniqueness(
        self, name: str, parent_id: Optional[str], exclude_id: Optional[str] = None
    ) -> None:
        """
        Ensure no duplicate (name, parent_id) pair, excluding an optional id.
        """
        query: dict = {"name": name, "parent_id": parent_id}
        if exclude_id:
            query["id"] = {"$ne": exclude_id}
        exists = await self.collection.find_one(query, projection={"_id": 1})
        if exists:
            raise ValueError(f"Category with name '{name}' already exists under the same parent")

    # ----------------------
    # CRUD (مثل قبل، با تزریق فایل)
    # ----------------------
    async def create(self, payload: CategoryCreate) -> Category:
        logger.debug("Creating category", extra={"payload": payload.model_dump()})

        # Validate parent
        if payload.parent_id:
            parent = await self.get(payload.parent_id)
            if not parent:
                raise ValueError(f"Parent category with id {payload.parent_id} does not exist")

        # Uniqueness on (name, parent)
        await self._check_name_uniqueness(payload.name, payload.parent_id)

        # Prepare document
        data = payload.model_dump(exclude_unset=True)
        data["id"] = str(uuid4())
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()

        # assign order if not provided
        if data.get("order") is None:
            data["order"] = await self._next_order(payload.parent_id)

        # 🔗 پر کردن خودکار image_url بر اساس image_id
        await self._autofill_image_url(data)

        await self.collection.insert_one(data)
        logger.info("Category created", extra={"category_id": data["id"]})
        return Category(**data)

    async def get(self, id_: str) -> Optional[Category]:
        logger.debug("Getting category", extra={"category_id": id_})
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

    async def update(self, id_: str, payload: CategoryUpdate) -> Optional[Category]:
        logger.debug("Updating category", extra={"category_id": id_, "payload": payload.model_dump(exclude_unset=True)})

        current = await self.collection.find_one({"id": id_})
        if not current:
            logger.warning("Category not found for update", extra={"category_id": id_})
            return None

        # Parent checks (loop + existence) — only if parent_id being changed (payload has it set)
        if "parent_id" in payload.model_fields_set:
            new_parent_id = payload.parent_id
            if new_parent_id:
                await self._validate_no_loop(id_, new_parent_id)
                parent = await self.get(new_parent_id)
                if not parent:
                    raise ValueError(f"Parent category with id {new_parent_id} does not exist")

        # Uniqueness on (name, parent_id) using new effective values
        new_name = payload.name if "name" in payload.model_fields_set else current.get("name")
        new_parent_id = (
            payload.parent_id if "parent_id" in payload.model_fields_set else current.get("parent_id")
        )
        await self._check_name_uniqueness(new_name, new_parent_id, exclude_id=id_)

        update_doc = payload.model_dump(exclude_unset=True)

        # 🔗 پر کردن/پاک کردن خودکار تصویر
        await self._autofill_image_url(update_doc)

        # If order provided, normalize siblings if collision exists
        if "order" in update_doc and update_doc["order"] is not None:
            if update_doc["order"] < 0:
                raise ValueError("Order cannot be negative")

            parent_id_for_order = new_parent_id
            existing = await self.collection.find_one(
                {"parent_id": parent_id_for_order, "order": update_doc["order"], "id": {"$ne": id_}},
                projection={"id": 1},
            )
            if existing:
                # Shift siblings down by 1 starting from desired order
                await self.collection.update_many(
                    {
                        "parent_id": parent_id_for_order,
                        "order": {"$gte": update_doc["order"]},
                        "id": {"$ne": id_},
                    },
                    {"$inc": {"order": 1}, "$set": {"updated_at": datetime.utcnow()}},
                )

        update_doc["updated_at"] = datetime.utcnow()

        # Return the updated document in one shot
        updated = await self.collection.find_one_and_update(
            {"id": id_},
            {"$set": update_doc},
            return_document=True,  # مثل نسخهٔ قبلی
        )

        if not updated:
            logger.warning("Category lost during update (race condition?)", extra={"category_id": id_})
            return None

        logger.info("Category updated", extra={"category_id": id_})
        return Category(**updated)

    async def delete(self, id_: str) -> bool:
        logger.debug("Deleting category", extra={"category_id": id_})

        current = await self.collection.find_one({"id": id_}, projection={"id": 1})
        if not current:
            return False

        # Prevent delete if has children
        has_children = await self.collection.find_one({"parent_id": id_}, projection={"_id": 1})
        if has_children:
            raise ValueError("Cannot delete category with children")

        result = await self.collection.delete_one({"id": id_})
        deleted = result.deleted_count > 0
        if deleted:
            logger.info("Category deleted", extra={"category_id": id_})
        else:
            logger.warning("Delete reported 0 deleted_count", extra={"category_id": id_})
        return deleted

    # ----------------------
    # Reordering (مثل قبل)
    # ----------------------
    async def reorder(self, payload: List[ReorderCategory]) -> bool:
        """
        Bulk reorder: all items must share the same parent.
        Payload items must have distinct 'order' values (>= 0).
        """
        logger.debug("Reordering multiple categories", extra={"count": len(payload)})

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

        # Apply updates
        now = datetime.utcnow()
        for item in payload:
            await self.collection.update_one(
                {"id": item.id},
                {"$set": {"order": item.order, "updated_at": now}},
            )

        logger.info("Bulk reorder applied", extra={"count": len(payload), "parent_id": list(parent_ids)[0]})
        return True

    async def reorder_single(self, category_id: str, new_order: int) -> bool:
        """
        Move a single category to a new 'order', shifting siblings in the range.
        """
        logger.debug("Reordering single category", extra={"category_id": category_id, "new_order": new_order})

        if new_order < 0:
            raise ValueError("Order cannot be negative")

        target = await self.get(category_id)
        if not target:
            logger.warning("Category not found for reorder", extra={"category_id": category_id})
            raise ValueError("Category not found")

        parent_id = target.parent_id
        current_order = target.order

        if new_order == current_order:
            return True

        # Determine shift direction
        direction = 1 if new_order > current_order else -1
        low, high = (current_order, new_order) if current_order <= new_order else (new_order, current_order)

        # Shift siblings within [low, high]
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

        # Place target at new_order
        await self.collection.update_one(
            {"id": category_id},
            {"$set": {"order": new_order, "updated_at": datetime.utcnow()}},
        )

        logger.info("Single reorder applied", extra={"category_id": category_id, "from": current_order, "to": new_order})
        return True


# Singleton instance
category_service = CategoryService()
