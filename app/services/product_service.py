from datetime import datetime
from typing import List, Optional, Tuple, Iterable
from uuid import UUID, uuid4

from fastapi import HTTPException
from pymongo import ASCENDING, DESCENDING

from app.db.mongo import db
from app.models.brand import Brand
from app.models.category import Category
from app.models.product import (
    Product,
    ProductCreate,
    ProductUpdate,
    ProductResponse,
)
from app.services.brand_service import brand_service
from app.services.category_service import category_service
from app.services.file_service import file_service
from app.services.base import MongoCRUD, _serialize


def _deleted_filter(include_deleted: bool) -> dict:
    """فیلتر رکوردهای حذف‌شده"""
    if include_deleted:
        return {}
    return {"$or": [{"deleted_at": None}, {"deleted_at": {"$exists": False}}]}


def _unique_uuids(items: Iterable[UUID]) -> List[UUID]:
    seen = set()
    out: List[UUID] = []
    for x in items or []:
        if x not in seen:
            out.append(x)
            seen.add(x)
    return out


class ProductService(MongoCRUD):
    def __init__(self):
        super().__init__(
            collection="products",
            model_cls=Product,
            create_cls=ProductCreate,
            update_cls=ProductUpdate,
        )

    # ---------------------------
    # Helpers
    # ---------------------------
    async def _validate_fk(
        self, brand_id: Optional[UUID], category_id: Optional[UUID]
    ) -> None:
        if brand_id:
            brand = await brand_service.get(brand_id)
            if not brand:
                raise HTTPException(status_code=404, detail="برند پیدا نشد.")
        if category_id:
            category = await category_service.get(category_id)
            if not category:
                raise HTTPException(status_code=404, detail="دسته‌بندی پیدا نشد.")

    async def _validate_images(
        self, primary_image_id: Optional[UUID], images: Optional[List[UUID]]
    ) -> List[UUID]:
        if primary_image_id:
            primary = await file_service.get(primary_image_id)
            if not primary:
                raise HTTPException(
                    status_code=400,
                    detail="شناسه تصویر اصلی (primary_image_id) نامعتبر است.",
                )

        valid_images: List[UUID] = []
        for fid in _unique_uuids(images or []):
            f = await file_service.get(fid)
            if not f:
                raise HTTPException(
                    status_code=400, detail="شناسه یکی از تصاویر (images) نامعتبر است."
                )
            valid_images.append(fid)

        return valid_images

    async def _populate(self, products: List[Product]) -> List[ProductResponse]:
        responses: List[ProductResponse] = []
        for p in products:
            data = p.model_dump()

            # Category
            if p.category_id:
                cat_doc = await db["categories"].find_one({"id": p.category_id})
                if cat_doc:
                    data["category"] = Category(**_serialize(cat_doc))

            # Brand
            if p.brand_id:
                brand_doc = await db["brands"].find_one({"id": p.brand_id})
                if brand_doc:
                    data["brand"] = Brand(**_serialize(brand_doc))

            # Images
            imgs = []
            if getattr(p, "primary_image_id", None):
                try:
                    primary = await file_service.get(p.primary_image_id)
                    if primary:
                        imgs.append(primary)
                except Exception:
                    pass
            for fid in (getattr(p, "images", []) or []):
                if getattr(p, "primary_image_id", None) and fid == p.primary_image_id:
                    continue
                try:
                    f_doc = await file_service.get(fid)
                    if f_doc:
                        imgs.append(f_doc)
                except Exception:
                    pass
            data["images"] = imgs

            responses.append(ProductResponse(**data))
        return responses

    # ---------------------------
    # CRUD
    # ---------------------------
    async def create(self, payload: ProductCreate) -> Product:
        now = datetime.utcnow()
        data = payload.model_dump(exclude_unset=True)

        # SKU uniqueness
        dup_q = {"sku": data["sku"], **_deleted_filter(False)}
        existing = await self.collection.find_one(dup_q)
        if existing:
            raise HTTPException(
                status_code=400, detail=f"محصول با کد {data['sku']} وجود دارد."
            )

        # FK checks
        await self._validate_fk(data.get("brand_id"), data.get("category_id"))

        # Images
        images = await self._validate_images(
            data.get("primary_image_id"), data.get("images")
        )
        data["images"] = images

        # system fields
        new_id = uuid4()
        data["_id"] = str(new_id)
        data["id"] = new_id
        data.setdefault("created_at", now)
        data.setdefault("updated_at", now)
        data.setdefault("deleted_at", None)

        await self.collection.insert_one(data)
        return Product(**data)

    async def update(self, id_: UUID, patch: ProductUpdate) -> Product | None:
        base_filter = {"_id": str(id_), **_deleted_filter(True)}
        current = await self.collection.find_one(base_filter)
        if not current:
            raise HTTPException(status_code=404, detail="محصول پیدا نشد.")

        if patch.brand_id or patch.category_id:
            await self._validate_fk(patch.brand_id, patch.category_id)

        if patch.sku:
            dup = await self.collection.find_one(
                {"sku": patch.sku, "_id": {"$ne": str(id_)}, **_deleted_filter(False)}
            )
            if dup:
                raise HTTPException(
                    status_code=400, detail=f"محصول با کد {patch.sku} وجود دارد."
                )

        patch_dict = patch.model_dump(exclude_unset=True)
        if "primary_image_id" in patch_dict or "images" in patch_dict:
            primary_image_id = patch_dict.get(
                "primary_image_id", current.get("primary_image_id")
            )
            images = patch_dict.get("images", current.get("images"))
            patch_dict["images"] = await self._validate_images(
                primary_image_id, images
            )

        patch_dict["updated_at"] = datetime.utcnow()

        await self.collection.update_one({"_id": str(id_)}, {"$set": patch_dict})
        doc = await self.collection.find_one({"_id": str(id_)})
        return Product(**_serialize(doc)) if doc else None

    async def delete(self, id_: UUID) -> bool:
        base = {"_id": str(id_), **_deleted_filter(False)}
        res = await self.collection.update_one(
            base,
            {"$set": {"deleted_at": datetime.utcnow(), "is_active": False}},
        )
        if res.modified_count == 0:
            raise HTTPException(status_code=404, detail="محصول پیدا نشد.")
        return True

    async def list(
        self,
        search: Optional[str] = None,
        brand_id: Optional[UUID] = None,
        category_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        is_active: Optional[bool] = None,
        include_deleted: bool = False,
        sort: Optional[str] = None,
        page: int = 1,
        limit: int = 10,
    ) -> Tuple[List[ProductResponse], int]:
        query: dict = {}
        query.update(_deleted_filter(include_deleted))

        if brand_id:
            query["brand_id"] = brand_id
        if category_id:
            query["category_id"] = category_id
        if is_active is not None:
            query["is_active"] = is_active
        if tags:
            query["tags"] = {"$in": tags}
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"full_name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
                {"tags": {"$regex": search, "$options": "i"}},
            ]

        cursor = self.collection.find(query)

        sort_map = {
            "name_asc": ("name", ASCENDING),
            "name_desc": ("name", DESCENDING),
            "created_asc": ("created_at", ASCENDING),
            "created_desc": ("created_at", DESCENDING),
        }
        key, direction = sort_map.get(sort or "created_desc")
        cursor = cursor.sort(key, direction)

        cursor = cursor.skip((page - 1) * limit).limit(limit)
        products = [self.model_cls(**_serialize(doc)) async for doc in cursor]
        total = await self.collection.count_documents(query)
        return await self._populate(products), total

    async def get(self, id_: UUID, include_deleted: bool = False) -> ProductResponse:
        base = {"_id": str(id_), **_deleted_filter(include_deleted)}
        doc = await self.collection.find_one(base)
        if not doc:
            raise HTTPException(status_code=404, detail="محصول پیدا نشد.")

        product = self.model_cls(**_serialize(doc))
        populated = await self._populate([product])
        return populated[0]


product_service = ProductService()
__all__ = ["ProductService", "product_service"]
